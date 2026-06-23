"""Step 5: reconcile gate — computed LAK sum must match the CRB summary block."""

import logging

logger = logging.getLogger(__name__)

TOLERANCE = 1.0


def reconcile(computed_lak: float, expected_lak: float, label: str) -> None:
    """Assert sum(LOCAL CURRENCY BAL) from the data rows matches the
    Total LAK reported in the file's own summary block.

    Raises ValueError with a clear computed-vs-expected message on mismatch —
    this is a hard stop, not a warning, since a mismatch means rows were
    dropped, misread, or double-counted upstream.
    """
    diff = abs(computed_lak - expected_lak)
    if diff > TOLERANCE:
        raise ValueError(
            f"RECONCILE FAILED ສຳລັບ {label}:\n"
            f"  ຄຳນວນໄດ້ (sum LOCAL CURRENCY BAL): {computed_lak:,.2f}\n"
            f"  ຄາດໝາຍ   (summary block Total LAK):  {expected_lak:,.2f}\n"
            f"  ຜິດດ່ຽງ: {diff:,.2f} (tolerance: {TOLERANCE})"
        )
    logger.info(
        f"RECONCILE OK ສຳລັບ {label}: "
        f"computed={computed_lak:,.2f}, expected={expected_lak:,.2f}, diff={diff:.4f}"
    )
