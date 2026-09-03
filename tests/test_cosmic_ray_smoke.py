"""Smoke deterministico: il mutante ``==`` → ``!=`` deve essere ucciso."""

from lab.mutation_smoke.subject import preserves_target


def test_preserves_target_non_scambia_uguale_con_diverso():
    assert preserves_target("R_target", "R_target") is True
    assert preserves_target("R_other", "R_target") is False
