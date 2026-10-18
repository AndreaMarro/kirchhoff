"""Il controllo di processo non può certificare prove assenti o superate."""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'ops/codex/verify.py'


@pytest.fixture
def modulo():
    assert SCRIPT.is_file(), 'Manca il verificatore neutrale con ricevute riproducibili.'
    spec = importlib.util.spec_from_file_location('codex_verify', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    (root / '.gitignore').write_text('.pytest_cache/\n__pycache__/\ncoverage.json\n')
    (root / 'source.py').write_text('VALUE = 1\n')
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    subprocess.run(['git', 'add', '.'], cwd=root, check=True)
    subprocess.run(['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '-qm', 'fixture originale'], cwd=root, check=True)
    return root


def prova_verde(argv, cwd, log, timeout):
    """Fixture del confine subprocess; gli oracoli restano quelli del repository."""
    log.write_text('fixture del comando\n')
    if '-m' in argv and 'pytest' in argv:
        report = next(a.split('=', 1)[1] for a in argv if a.startswith('--junitxml='))
        Path(report).write_text('<testsuites><testsuite tests="3" failures="0" errors="0" skipped="1"/></testsuites>')
        target = next(a.split('json:', 1)[1] for a in argv if a.startswith('--cov-report=json:'))
        Path(target).write_text('{"fixture": true}')
    return {'exit_code': 0, 'timed_out': False, 'elapsed_seconds': 0.01}


def test_un_comando_fallito_conserva_exit_e_log(modulo, tmp_path):
    log = tmp_path / 'failure.log'
    result = modulo.esegui([sys.executable, '-c', 'print("controesempio"); raise SystemExit(7)'],
                           tmp_path, log, 5)
    assert result['exit_code'] == 7
    assert result['timed_out'] is False
    assert 'controesempio' in log.read_text()


def test_timeout_non_diventa_pass(modulo, tmp_path):
    result = modulo.esegui([sys.executable, '-c', 'import time; time.sleep(30)'],
                           tmp_path, tmp_path / 'timeout.log', 0.05)
    assert result['timed_out'] is True
    assert result['exit_code'] != 0


def test_timeout_termina_anche_un_figlio_che_ignora_term(modulo, tmp_path):
    marker = tmp_path / 'figlio-sopravvissuto'
    child = ('import signal,time,pathlib; signal.signal(signal.SIGTERM,signal.SIG_IGN); '
             f'time.sleep(0.6); pathlib.Path({str(marker)!r}).write_text("vivo")')
    parent = f'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(30)'
    result = modulo.esegui([sys.executable, '-c', parent], tmp_path, tmp_path / 'children.log', 0.2)
    time.sleep(0.7)
    assert result['timed_out'] is True
    assert not marker.exists(), 'Il timeout ha lasciato in esecuzione un processo figlio.'


def test_test_rossi_non_riusano_coverage_vecchia(modulo, repository, tmp_path):
    (repository / 'coverage.json').write_text('{"totals": {"percent_covered": 100}}')
    calls = []

    def rosso(argv, cwd, log, timeout):
        calls.append(argv)
        result = prova_verde(argv, cwd, log, timeout)
        if 'pytest' in argv:
            result['exit_code'] = 1
        return result

    output = tmp_path / 'run'
    receipt = modulo.verifica(repository, output, runner=rosso)
    assert receipt['status'] == 'CHECKS_FAILED'
    assert len(calls) == 2  # catena, poi test; nessun oracolo sul report stantio
    assert receipt['checks'][-1]['status'] == 'FAIL'
    assert json.loads((output / 'receipt.json').read_text())['status'] == 'CHECKS_FAILED'


def test_suite_solo_saltata_non_e_verifica(modulo, repository, tmp_path):
    def saltata(argv, cwd, log, timeout):
        result = prova_verde(argv, cwd, log, timeout)
        if 'pytest' in argv:
            report = next(a.split('=', 1)[1] for a in argv if a.startswith('--junitxml='))
            Path(report).write_text('<testsuites><testsuite tests="2" failures="0" errors="0" skipped="2"/></testsuites>')
        return result

    receipt = modulo.verifica(repository, tmp_path / 'run', runner=saltata)
    assert receipt['status'] == 'CHECKS_FAILED'
    assert receipt['tests']['passed'] == 0


def test_sorgenti_mutate_in_corsa_invalidano_la_ricevuta(modulo, repository, tmp_path):
    def mutazione(argv, cwd, log, timeout):
        result = prova_verde(argv, cwd, log, timeout)
        if 'pytest' in argv:
            (repository / 'source.py').write_text('VALUE = 2\n')
        return result

    receipt = modulo.verifica(repository, tmp_path / 'run', runner=mutazione)
    assert receipt['status'] == 'CHECKS_FAILED'
    assert receipt['snapshot_before']['sha256'] != receipt['snapshot_after']['sha256'], receipt['checks']


def test_freschezza_usa_orologio_del_filesystem_non_wall_clock(modulo, repository, tmp_path, monkeypatch):
    # Il wall clock può essere avanti rispetto al timestamp pubblicato dal filesystem.
    # Anche un report appena creato diventava allora «precedente» al comando.
    real_clock = time.time_ns
    monkeypatch.setattr(modulo.time, 'time_ns', lambda: real_clock() + 10_000_000_000)
    receipt = modulo.verifica(repository, tmp_path / 'run', runner=prova_verde)
    assert receipt['status'] == 'CHECKS_PASSED', receipt['checks']
    assert len(receipt['checks']) == 4


def test_skip_e_limiti_restano_espliciti(modulo, repository, tmp_path):
    receipt = modulo.verifica(repository, tmp_path / 'run', runner=prova_verde)
    assert receipt['status'] == 'CHECKS_PASSED'
    assert receipt['tests'] == {'total': 3, 'passed': 2, 'skipped': 1, 'failed': 0, 'errors': 0}
    assert len(receipt['checks']) == 4
    assert receipt['product_ready'] is False
    assert 'independent_review' in receipt['not_tested']


def test_output_in_repo_o_riutilizzato_rifiutato(modulo, repository, tmp_path):
    with pytest.raises(ValueError, match='estern'):
        modulo.verifica(repository, repository / 'artifacts', runner=prova_verde)
    output = tmp_path / 'run'
    output.mkdir()
    with pytest.raises(FileExistsError):
        modulo.verifica(repository, output, runner=prova_verde)


def test_holdout_non_letto_e_symlink_non_seguito(modulo, repository, tmp_path):
    protected = repository / 'reference-set/holdout'
    protected.mkdir(parents=True)
    secret = protected / 'non_leggere.txt'
    secret.write_text('fixture sintetica che non deve essere letta')
    link = repository / 'link-esterno'
    link.symlink_to(tmp_path / 'non-esiste')
    snapshot = modulo.fotografia(repository)
    secret.write_text('altri byte nel perimetro escluso')
    assert modulo.fotografia(repository)['sha256'] == snapshot['sha256']


def test_antenato_symlink_non_puo_far_leggere_byte_esterni(modulo, repository, tmp_path):
    package = repository / 'package'
    package.mkdir()
    (package / 'data.py').write_text('originale\n')
    subprocess.run(['git', 'add', 'package'], cwd=repository, check=True)
    (package / 'data.py').unlink()
    package.rmdir()
    external = tmp_path / 'esterno'
    external.mkdir()
    (external / 'data.py').write_text('byte esterni sintetici\n')
    package.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match='simbolic'):
        modulo.fotografia(repository)


@pytest.mark.parametrize('target', ['coverage.json', 'pytest.xml'])
def test_report_con_symlink_non_puo_essere_prova_fresca(modulo, repository, tmp_path, target):
    old = tmp_path / 'vecchio-report'
    output = tmp_path / 'run'

    def collegato(argv, cwd, log, timeout):
        result = prova_verde(argv, cwd, log, timeout)
        if 'pytest' in argv:
            path = output / target
            old.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(old)
        return result

    receipt = modulo.verifica(repository, output, runner=collegato)
    assert receipt['status'] == 'CHECKS_FAILED'
    assert receipt['checks'][-1]['status'] == 'FAIL'


def test_report_precedente_non_puo_essere_prova_fresca(modulo, repository, tmp_path):
    output = tmp_path / 'run'

    def precedente(argv, cwd, log, timeout):
        result = prova_verde(argv, cwd, log, timeout)
        if 'pytest' in argv:
            os.utime(output / 'coverage.json', ns=(1, 1))
        return result

    receipt = modulo.verifica(repository, output, runner=precedente)
    assert receipt['status'] == 'CHECKS_FAILED'
    assert 'precedente' in receipt['checks'][-1]['evidence_error']


def test_faccia_cli_espone_verifica_senza_avviare_modelli():
    root = SCRIPT.parents[2]
    result = subprocess.run(['bash', str(root / 'ops/loop/kirchhoff-loop'), 'verify',
                             '--output', str(root / 'output-non-consentito')],
                            cwd=root, capture_output=True, text=True, timeout=5)
    assert result.returncode == 2, result.stderr
    assert 'esterna' in result.stderr
    assert not (root / 'output-non-consentito').exists()
