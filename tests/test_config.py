"""Configurazione: valida all'avvio, o non si parte.

Il punto non è avere una configurazione. È che tre vincoli che finora vivevano
soltanto nella prosa del piano diventino qui condizioni di avvio: almeno tre passi
di estrazione (D4, AD-12), immagini cancellate entro 72 ore (FR-30), dati in Unione
Europea (NFR-14). Un vincolo scritto e non imposto dura quanto l'attenzione di chi
scrive — è la lezione R1 della retrospettiva di Epic 1.
"""

import pytest

from kirchhoff.config import ConfigError, Settings, load_settings

VALIDO = {
    "KIRCHHOFF_ENV": "dev",
    "KIRCHHOFF_DATA_REGION": "eu-west-1",
    "KIRCHHOFF_EXTRACTION_PASSES": "3",
    "KIRCHHOFF_IMAGE_TTL_HOURS": "72",
}


def con(**override) -> dict:
    return {**VALIDO, **override}


def test_configurazione_valida():
    s = load_settings(con())
    assert isinstance(s, Settings)
    assert s.env == "dev"
    assert s.data_region == "eu-west-1"
    assert s.extraction_passes == 3
    assert s.image_ttl_hours == 72


def test_la_configurazione_e_congelata():
    s = load_settings(con())
    with pytest.raises(Exception):
        s.env = "prod"          # type: ignore[misc]


def test_variabile_obbligatoria_assente():
    ambiente = con()
    del ambiente["KIRCHHOFF_ENV"]
    with pytest.raises(ConfigError, match="KIRCHHOFF_ENV"):
        load_settings(ambiente)


def test_valore_fuori_dall_insieme_ammesso():
    with pytest.raises(ConfigError, match="KIRCHHOFF_ENV"):
        load_settings(con(KIRCHHOFF_ENV="collaudo"))


def test_intero_malformato():
    with pytest.raises(ConfigError, match="intero"):
        load_settings(con(KIRCHHOFF_EXTRACTION_PASSES="tre"))


def test_meno_di_tre_pass_rifiutati():
    """L'ambiguita' si misura come disaccordo fra almeno tre pass, o non si misura (D4, AD-12)."""
    with pytest.raises(ConfigError, match="almeno 3"):
        load_settings(con(KIRCHHOFF_EXTRACTION_PASSES="2"))
    assert load_settings(con(KIRCHHOFF_EXTRACTION_PASSES="5")).extraction_passes == 5


def test_ttl_oltre_settantadue_ore_rifiutato():
    with pytest.raises(ConfigError, match="72"):
        load_settings(con(KIRCHHOFF_IMAGE_TTL_HOURS="96"))
    assert load_settings(con(KIRCHHOFF_IMAGE_TTL_HOURS="24")).image_ttl_hours == 24


def test_ttl_non_positivo_rifiutato():
    with pytest.raises(ConfigError, match="positiv"):
        load_settings(con(KIRCHHOFF_IMAGE_TTL_HOURS="0"))


def test_regione_fuori_unione_europea_rifiutata():
    with pytest.raises(ConfigError, match="us-east-1"):
        load_settings(con(KIRCHHOFF_DATA_REGION="us-east-1"))


def test_il_messaggio_dice_cosa_si_aspettava():
    with pytest.raises(ConfigError) as e:
        load_settings(con(KIRCHHOFF_ENV="collaudo"))
    testo = str(e.value)
    assert "collaudo" in testo
    assert "dev" in testo and "prod" in testo


def test_il_port_dell_orologio_non_e_importato_dal_dominio():
    """AD-17: un solo orologio, iniettato. Il dominio non lo conosce nemmeno."""
    from kirchhoff.ports.clock import ClockPort
    assert hasattr(ClockPort, "now")


def test_avvio_dall_ambiente_reale(monkeypatch):
    """Il percorso d'avvio vero: `os.environ`, non un dizionario di comodo."""
    for k, v in VALIDO.items():
        monkeypatch.setenv(k, v)
    from kirchhoff.config import from_environment
    assert from_environment().extraction_passes == 3

    monkeypatch.setenv("KIRCHHOFF_EXTRACTION_PASSES", "1")
    with pytest.raises(ConfigError, match="almeno 3"):
        from_environment()


def test_la_soglia_non_si_aggira_costruendo_il_tipo_a_mano():
    """AD-12: `K >= 3` e' imposto dal codice, non da un percorso di caricamento."""
    with pytest.raises(ConfigError, match="almeno 3"):
        Settings(env="dev", data_region="eu-west-1",
                 extraction_passes=1, image_ttl_hours=24)
    with pytest.raises(ConfigError, match="72"):
        Settings(env="dev", data_region="eu-west-1",
                 extraction_passes=3, image_ttl_hours=96)
