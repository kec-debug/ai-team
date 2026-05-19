"""mvp-014: verify the official-values gap document exists and is safe."""

import pathlib


DOC_PATH = pathlib.Path(__file__).resolve().parents[3] / "docs" / "kis" / "MISSING_OFFICIAL_VALUES.md"


def test_missing_official_values_file_exists():
    assert DOC_PATH.is_file(), f"expected {DOC_PATH} to exist"


def test_missing_official_values_has_required_sections():
    text = DOC_PATH.read_text(encoding="utf-8")
    for header in (
        "OAuth",
        "해외주식",
        "모의투자 주문",
        "Confirmed",
    ):
        assert header in text, f"missing required marker: {header}"


def test_missing_official_values_does_not_leak_real_secrets():
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "<TBD>" in text
    forbidden_values = (
        "PS" + "NFD",
        "PK" + "ID",
        "AK" + "IA",
        "s" + "k-",
        "gh" + "p_",
    )
    for forbidden in forbidden_values:
        assert forbidden not in text
