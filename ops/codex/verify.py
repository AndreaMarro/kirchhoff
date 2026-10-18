#!/usr/bin/env python3
"""Esegue i gate deterministici esistenti, senza avviare un modello o promuovere codice.

Verificatore candidato: non sostituisce l'autorità del Loop, la readiness o la review.
Invocare nell'ambiente frozen del progetto e scegliere un output nuovo, esterno al repo.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


RADICE = Path(__file__).resolve().parents[2]


def fotografia(root: Path) -> dict:
    """Identifica anche sorgenti sporchi; esclude l'holdout e non segue symlink."""
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=root)

    names = sorted(set(git('ls-files', '-c', '-o', '--exclude-standard', '-z').split(b'\0')) - {b''})
    digest = hashlib.sha256()
    excluded = 0
    for raw in names:
        relative = Path(os.fsdecode(raw))
        if tuple(part.casefold() for part in relative.parts[:2]) == ('reference-set', 'holdout'):
            excluded += 1
            continue
        if any((root / parent).is_symlink() for parent in relative.parents):
            raise ValueError('Antenato con collegamento simbolico: ' + str(relative))
        path = root / relative
        if path.is_symlink():
            value = b'link\0' + os.fsencode(os.readlink(path))
        elif path.is_file():
            value = b'file\0' + path.read_bytes()
        else:
            value = b'assente'
        digest.update(len(raw).to_bytes(8, 'big') + raw)
        digest.update(hashlib.sha256(value).digest())
    return {'head': git('rev-parse', 'HEAD').decode().strip(),
            'sha256': digest.hexdigest(), 'holdout_excluded': excluded,
            'worktree_status': git('status', '--porcelain=v1').decode()}


def esegui(argv: list[str], cwd: Path, log: Path, timeout: float) -> dict:
    """Conserva exit e log; al timeout termina anche i processi figli del comando."""
    started = time.monotonic()
    timed_out = False
    with log.open('wb') as stream:
        try:
            process = subprocess.Popen(argv, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    code = process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    code = None
                finally:
                    # Il padre può uscire al TERM lasciando un figlio che lo ignora.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if code is None:
                    code = process.wait()
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
        except OSError as exc:
            stream.write(str(exc).encode())
            code = 127
    return {'exit_code': code, 'timed_out': timed_out,
            'elapsed_seconds': round(time.monotonic() - started, 6)}


def conteggi(data: bytes) -> dict:
    """Legge i contatori JUnit, senza contar punti nell'output della coverage."""
    root = ET.fromstring(data)
    suites = [s for s in root.iter('testsuite') if not s.findall('testsuite')]
    if not suites:
        raise ValueError('Il report JUnit non contiene una suite.')
    totals = {key: sum(int(s.get(attribute, '0')) for s in suites)
              for key, attribute in [('total', 'tests'), ('skipped', 'skipped'),
                                     ('failed', 'failures'), ('errors', 'errors')]}
    totals['passed'] = totals['total'] - totals['skipped'] - totals['failed'] - totals['errors']
    if min(totals.values()) < 0:
        raise ValueError('Contatori JUnit incoerenti.')
    return totals


def prova_fresca(path: Path, output: Path, started_ns: int) -> bytes:
    """Rifiuta alias e file precedenti prima di leggerne il contenuto."""
    if path.is_symlink() or path.resolve().parent != output:
        raise ValueError('Report non confinato nella corsa: ' + path.name)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mtime_ns < started_ns:
            raise ValueError('Report non regolare o precedente alla corsa: ' + path.name)
        return stream.read()


def verifica(root: Path, output: Path, *, runner=esegui, timeout: float = 900) -> dict:
    """Una corsa finita; un errore impedisce di consumare prove di passi successivi."""
    root, output = root.resolve(), output.resolve()
    if output.is_relative_to(root):
        raise ValueError('Le ricevute richiedono una directory esterna al repository.')
    if timeout <= 0:
        raise ValueError('Il timeout deve essere positivo.')
    output.mkdir(parents=True, exist_ok=False)
    before = fotografia(root)
    receipt = {'schema': 'kirchhoff-local-checks.v1', 'started_at': datetime.now(timezone.utc).isoformat(),
               'snapshot_before': before, 'python': sys.version, 'checks': [], 'tests': None,
               'status': 'CHECKS_FAILED', 'product_ready': False,
               'process_tree_isolation': False,
               'timeout_scope': 'initial_process_group_only; independently daemonized children are not contained',
               'not_tested': ['independent_review', 'exact_sha_remote_ci', 'browser_flow',
                              'teacher_content_approval', 'hardware', 'legacy_retirement']}
    report, coverage = output / 'pytest.xml', output / 'coverage.json'
    plan = [
        ('chain', [sys.executable, str(root / 'scripts/bmad_chain.py'), 'verifica', '--con-loop'], root),
        ('pytest', [sys.executable, '-m', 'pytest', 'tests', '--junitxml=' + str(report),
                    '--cov-report=json:' + str(coverage)], root),
        ('coverage', [sys.executable, str(root / 'scripts/check_domain_coverage.py'),
                      '--baseline', str(root / 'docs/quality/coverage-baseline.json')], output),
        ('boundaries', [sys.executable, str(root / 'scripts/check_boundaries.py')], root),
    ]
    for name, argv, cwd in plan:
        log = output / (name + '.log')
        print('Verifica: ' + name, flush=True)
        # Confronta timestamp prodotti dallo stesso filesystem: il wall clock può
        # avere precisione/offset diversi e far apparire vecchio un file nuovo.
        marker = output / ('.' + name + '.start')
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'wb') as stream:
            started_ns = os.fstat(stream.fileno()).st_mtime_ns
        result = runner(argv, cwd, log, timeout)
        row = {'name': name, 'argv': argv, 'cwd': str(cwd), **result,
               'evidence_started_ns': started_ns, 'evidence_clock': 'filesystem_marker',
               'log': str(log),
               'status': 'PASS' if result['exit_code'] == 0 and not result['timed_out'] else 'FAIL'}
        receipt['checks'].append(row)
        try:
            row['log_sha256'] = hashlib.sha256(prova_fresca(log, output, started_ns)).hexdigest()
        except (OSError, ValueError) as exc:
            row.update(status='FAIL', evidence_error=str(exc))
        if row['status'] == 'PASS' and name == 'pytest':
            try:
                junit_bytes = prova_fresca(report, output, started_ns)
                coverage_bytes = prova_fresca(coverage, output, started_ns)
                receipt['tests'] = conteggi(junit_bytes)
                counts = receipt['tests']
                if counts['passed'] == 0 or counts['failed'] or counts['errors'] or not coverage.is_file():
                    raise ValueError('Test eseguiti o nuovo report di copertura mancanti.')
                row['coverage_sha256'] = hashlib.sha256(coverage_bytes).hexdigest()
                row['junit_sha256'] = hashlib.sha256(junit_bytes).hexdigest()
            except (OSError, ValueError, ET.ParseError) as exc:
                row.update(status='FAIL', evidence_error=str(exc))
        if row['status'] != 'PASS':
            break
    receipt['snapshot_after'] = fotografia(root)
    receipt['source_unchanged'] = before == receipt['snapshot_after']
    if (len(receipt['checks']) == len(plan) and all(c['status'] == 'PASS' for c in receipt['checks'])
            and receipt['source_unchanged']):
        receipt['status'] = 'CHECKS_PASSED'
    receipt['finished_at'] = datetime.now(timezone.utc).isoformat()
    (output / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=900, help='Secondi massimi per ciascuno dei quattro comandi.')
    args = parser.parse_args()
    try:
        receipt = verifica(RADICE, args.output, timeout=args.timeout)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('VERIFICA NON ESEGUITA: ' + str(exc), file=sys.stderr)
        return 2
    print(receipt['status'] + ' — ' + str(args.output / 'receipt.json'))
    return 0 if receipt['status'] == 'CHECKS_PASSED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
