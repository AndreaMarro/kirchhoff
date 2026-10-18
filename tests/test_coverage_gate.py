"""Il gate reale deve rifiutare regressioni anche sopra il minimo globale."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/check_domain_coverage.py'


def run_gate(tmp_path, covered=975, total=1000, *, branches=0, covered_branches=0,
             domain_percent=100, branch_coverage=True, baseline=None, mutate=None):
    report = {
        'meta': {'branch_coverage': branch_coverage},
        'totals': {'covered_lines': covered, 'num_statements': total,
                   'covered_branches': covered_branches, 'num_branches': branches,
                   'percent_covered': 100},  # deliberatamente non autorevole
        'files': {'src/kirchhoff/domain/example.py': {
            'summary': {'percent_covered': domain_percent,
                        'covered_lines': domain_percent, 'num_statements': 100,
                        'covered_branches': 0, 'num_branches': 0},
            'missing_lines': [1] if domain_percent < 100 else [],
            'missing_branches': [],
        }},
    }
    if mutate:
        mutate(report)
    (tmp_path / 'coverage.json').write_text(json.dumps(report))
    pinned = baseline or {'schema': 'kirchhoff-coverage-baseline.v1',
                          'covered': 975, 'total': 1000}
    baseline_path = tmp_path / 'baseline.json'
    baseline_path.write_text(json.dumps(pinned))
    return subprocess.run([sys.executable, str(SCRIPT), '--baseline', str(baseline_path)],
                          cwd=tmp_path, capture_output=True, text=True)


@pytest.mark.parametrize(('covered', 'total'), [(975, 1000), (1950, 2000), (976, 1000)])
def test_baseline_uguale_o_migliore_passano(tmp_path, covered, total):
    result = run_gate(tmp_path, covered, total)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(('covered', 'total'), [(974, 1000), (974999, 1000000)])
def test_regressione_sopra_95_e_arrotondamento_non_passano(tmp_path, covered, total):
    result = run_gate(tmp_path, covered, total)
    assert result.returncode == 1, result.stdout + result.stderr


def test_minimo_globale_95_resta_anche_con_baseline_inferiore(tmp_path):
    result = run_gate(tmp_path, 94, 100, baseline={
        'schema': 'kirchhoff-coverage-baseline.v1', 'covered': 90, 'total': 100})
    assert result.returncode == 1, result.stdout + result.stderr


def test_rami_scoperti_contano_anche_con_righe_tutte_coperte(tmp_path):
    result = run_gate(tmp_path, 100, 100, branches=100, covered_branches=90)
    assert result.returncode == 1, result.stdout + result.stderr


def test_dominio_non_puo_regredire_anche_se_globale_migliora(tmp_path):
    result = run_gate(tmp_path, 999, 1000, domain_percent=99)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize('percent', [100, 101, float('nan')])
def test_percentuale_dominio_non_nasconde_righe_scoperte(tmp_path, percent):
    def forge(report):
        report['files']['src/kirchhoff/domain/example.py']['summary']['percent_covered'] = percent
    result = run_gate(tmp_path, 999, 1000, domain_percent=99, mutate=forge)
    assert result.returncode == 1, result.stdout + result.stderr


def test_ramo_dominio_scoperto_non_nascosto_da_percentuale_100(tmp_path):
    def forge(report):
        report['files']['src/kirchhoff/domain/example.py']['summary'].update(
            covered_branches=1, num_branches=2)
    result = run_gate(tmp_path, 999, 1000, mutate=forge)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize('change', [
    lambda r: r.update(totals={}),
    lambda r: r['totals'].update(covered_lines=True),
    lambda r: r['totals'].update(covered_lines=1001),
    lambda r: r['totals'].update(num_branches=-1),
    lambda r: r.update(files={}),
    lambda r: r['meta'].update(branch_coverage=False),
])
def test_report_incompleto_o_incoerente_non_e_un_verde(tmp_path, change):
    result = run_gate(tmp_path, mutate=change)
    assert result.returncode == 1, result.stdout + result.stderr


@pytest.mark.parametrize('baseline', [
    {'schema': 'unknown', 'covered': 975, 'total': 1000},
    {'schema': 'kirchhoff-coverage-baseline.v1', 'covered': 0, 'total': 0},
    {'schema': 'kirchhoff-coverage-baseline.v1', 'covered': 1001, 'total': 1000},
])
def test_baseline_non_valida_non_disabilita_la_guardia(tmp_path, baseline):
    result = run_gate(tmp_path, baseline=baseline)
    assert result.returncode == 1, result.stdout + result.stderr


def test_baseline_mancante_produce_rifiuto_leggibile(tmp_path):
    (tmp_path / 'coverage.json').write_text('{}')
    result = subprocess.run([sys.executable, str(SCRIPT), '--baseline', 'missing.json'],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1
    assert 'Traceback' not in result.stderr
