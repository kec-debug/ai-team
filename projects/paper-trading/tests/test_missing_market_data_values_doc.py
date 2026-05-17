import pathlib
import re


DOC_PATH = pathlib.Path(__file__).resolve().parents[3] / "docs" / "kis" / "MISSING_MARKET_DATA_VALUES.md"


def test_doc_exists():
    assert DOC_PATH.is_file(), f"missing: {DOC_PATH}"


def test_doc_has_required_sections():
    text = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "현재가",
        "Quote",
        "응답 필드",
        "호가단위",
        "Confirmed",
        "<TBD>",
    ):
        assert marker in text, f"missing marker: {marker}"


def test_doc_has_confirmed_status_mix():
    text = DOC_PATH.read_text(encoding="utf-8")
    yes_cells = re.findall(r"\|\s*yes\s*\|", text)
    unconfirmed_cells = re.findall(r"\|\s*(?:no|partial|<TBD>)\s*\|", text)
    assert len(yes_cells) >= 5, (
        f"expected >=5 Confirmed-yes rows after KIS_1, got {len(yes_cells)}"
    )
    assert len(unconfirmed_cells) >= 1, (
        f"expected >=1 Confirmed-no/partial/<TBD> row to remain, got {len(unconfirmed_cells)}"
    )


def test_doc_does_not_leak_real_secrets():
    text = DOC_PATH.read_text(encoding="utf-8")
    for forbidden in ("PSNFD", "PKID", "AKIA", "sk-", "ghp_"):
        assert forbidden not in text, f"forbidden prefix present: {forbidden}"
    assert "appkey=" not in text, "real-key-style assignment present"
    assert "appsecret=" not in text, "real-secret-style assignment present"
    assert "Bearer eyJ" not in text, "JWT-style bearer token present"
    assert re.search(r"\d{8}-\d{2}", text) is None, "account-number pattern present"
