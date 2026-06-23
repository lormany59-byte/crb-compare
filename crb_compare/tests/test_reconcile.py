import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reconcile import reconcile  # noqa: E402

# Test fixture values from SPEC §5
BASE_TOTAL_LAK = 591235357034.00       # CRB_2026-05-18
COMPARE_TOTAL_LAK = 598124409471.71    # CRB_2026-05-19


def test_reconcile_exact_match():
    reconcile(BASE_TOTAL_LAK, BASE_TOTAL_LAK, "CRB_2026-05-18")


def test_reconcile_within_tolerance():
    reconcile(BASE_TOTAL_LAK, BASE_TOTAL_LAK + 0.5, "CRB_2026-05-18")


def test_reconcile_fixture_base():
    reconcile(BASE_TOTAL_LAK, BASE_TOTAL_LAK, "CRB_2026-05-18")


def test_reconcile_fixture_compare():
    reconcile(COMPARE_TOTAL_LAK, COMPARE_TOTAL_LAK, "CRB_2026-05-19")


def test_reconcile_fails_outside_tolerance():
    with pytest.raises(ValueError, match="RECONCILE FAILED"):
        reconcile(BASE_TOTAL_LAK, COMPARE_TOTAL_LAK, "CRB_2026-05-18")


def test_reconcile_fails_just_over_tolerance():
    with pytest.raises(ValueError, match="RECONCILE FAILED"):
        reconcile(BASE_TOTAL_LAK, BASE_TOTAL_LAK + 1.01, "CRB_2026-05-18")
