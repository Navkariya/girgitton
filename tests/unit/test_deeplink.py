"""girgitton:// deep link parser testlari."""

from __future__ import annotations

from girgitton.app.deeplink import parse_deep_link


def test_parse_full_url() -> None:
    result = parse_deep_link("girgitton://connect?code=ABC123&server=http://localhost:8080")
    assert result["code"] == "ABC123"
    assert result["server"] == "http://localhost:8080"


def test_parse_only_code() -> None:
    assert parse_deep_link("girgitton://connect?code=XYZ") == {"code": "XYZ"}


def test_parse_unrelated_url() -> None:
    assert parse_deep_link("https://example.com/x?code=1") == {}


def test_parse_empty_query() -> None:
    assert parse_deep_link("girgitton://connect") == {}
