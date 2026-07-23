from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.config import Settings


def test_catalog_years_default_to_current_and_previous_year() -> None:
    current_year = datetime.now(UTC).year
    settings = Settings(
        gdc_vault_years_raw="",
        advances_years_raw="",
        dry_run=True,
    )

    assert settings.gdc_vault_years == [current_year, current_year - 1]
    assert settings.advances_years == [current_year, current_year - 1]


def test_catalog_years_preserve_order_and_remove_duplicates() -> None:
    settings = Settings(
        gdc_vault_years_raw="2026, 2025, 2026",
        advances_years_raw="2025,2024",
        dry_run=True,
    )

    assert settings.gdc_vault_years == [2026, 2025]
    assert settings.advances_years == [2025, 2024]


def test_catalog_years_reject_invalid_values() -> None:
    settings = Settings(gdc_vault_years_raw="latest", dry_run=True)

    with pytest.raises(ValueError, match="GDC_VAULT_YEARS"):
        _ = settings.gdc_vault_years
