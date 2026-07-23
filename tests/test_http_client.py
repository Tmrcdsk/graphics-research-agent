from __future__ import annotations

import httpx

from app.sources.http_client import decode_response_text


def test_decode_response_text_falls_back_to_windows_1252_without_charset() -> None:
    response = httpx.Response(
        200,
        content=b"Smolder \x97 Real-Time Volumetric Effect Rendering",
        headers={"Content-Type": "text/html"},
    )

    assert decode_response_text(response) == (
        "Smolder \N{EM DASH} Real-Time Volumetric Effect Rendering"
    )


def test_decode_response_text_honors_explicit_charset() -> None:
    response = httpx.Response(
        200,
        content="Gr\u00fc\u00dfe".encode("iso-8859-1"),
        headers={"Content-Type": "text/html; charset=iso-8859-1"},
    )

    assert decode_response_text(response) == "Gr\u00fc\u00dfe"


def test_decode_response_text_uses_utf8_when_charset_is_missing() -> None:
    response = httpx.Response(
        200,
        content="\u5b9e\u65f6\u6e32\u67d3".encode(),
        headers={"Content-Type": "text/html"},
    )

    assert decode_response_text(response) == "\u5b9e\u65f6\u6e32\u67d3"
