"""Step 1: read, clean, and group a single CRB export file."""

import logging
import warnings
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "CONTRACT",
    "BRANCH",
    "CURRENCY",
    "CUSTOMER",
    "CONTRACT BAL",
    "LOCAL CURRENCY BAL",
    "PROCESSING DATE",
]


def _extract_summary_lak(path) -> float:
    """Pull Total LAK out of the summary block (row 5 of the sheet).

    Row 5 holds the grand total in LAK (all currencies converted), which is
    always the largest positive number on that row — bigger than any single
    per-currency subtotal above it.
    """
    df_raw = pd.read_excel(path, sheet_name="CRBreport", header=None, nrows=5)
    row5 = df_raw.iloc[4]

    candidates = []
    for col_idx, val in enumerate(row5):
        if pd.isna(val):
            continue
        if isinstance(val, (int, float)):
            num = float(val)
        elif isinstance(val, str):
            cleaned = val.replace(",", "").strip()
            try:
                num = float(cleaned)
            except ValueError:
                continue
        else:
            continue
        if num > 0:
            candidates.append((col_idx, num))

    if not candidates:
        raise ValueError(
            f"ບໍ່ພົບ Total LAK ໃນ summary block ແຖວ 5 ຂອງໄຟລ໌ {Path(path).name}"
        )

    col_idx, total_lak = max(candidates, key=lambda x: x[1])
    logger.info(f"  Summary Total LAK (row 5, col {col_idx}): {total_lak:,.2f}")
    return total_lak


def read_crb(path) -> tuple[pd.DataFrame, float, str]:
    """Read and clean one CRB export file.

    Returns:
        grouped: one row per CONTRACT with BAL / LAKBAL / BRANCH / CURRENCY / CUSTOMER
        total_lak: Total LAK pulled from the summary block (for reconcile)
        processing_date: YYYYMMDD string
    """
    path = Path(path)
    logger.info(f"Reading {path.name}...")

    total_lak = _extract_summary_lak(path)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        df = pd.read_excel(
            path,
            sheet_name="CRBreport",
            header=5,  # row 6 (0-indexed) is the real header
            dtype={
                "CONTRACT": str,
                "GL LINE": str,
                "BOL LINE": str,
            },
        )

    logger.info(f"  Read {len(df):,} rows")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"ໄຟລ໌ {path.name} ຂາດຄໍລໍາ: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["CONTRACT"] = df["CONTRACT"].astype(str).str.strip()

    df["CONTRACT BAL"] = pd.to_numeric(df["CONTRACT BAL"], errors="coerce").fillna(0.0)
    df["LOCAL CURRENCY BAL"] = pd.to_numeric(
        df["LOCAL CURRENCY BAL"], errors="coerce"
    ).fillna(0.0)
    df["CURRENCY"] = df["CURRENCY"].fillna("").astype(str).str.strip()
    df["BRANCH"] = df["BRANCH"].fillna("").astype(str).str.strip()
    df["CUSTOMER"] = df["CUSTOMER"].fillna("").astype(str).str.strip()

    empty_currency = df["CURRENCY"] == ""
    if empty_currency.any():
        logger.warning(
            f"  {empty_currency.sum()} ແຖວ CURRENCY ຫວ່າງ — ຖືເປັນ 0/ບໍ່ນັບ threshold"
        )

    proc_dates = df["PROCESSING DATE"].dropna().astype(str).str.strip()
    proc_dates = proc_dates[proc_dates != ""]
    if proc_dates.empty:
        raise ValueError(f"ບໍ່ພົບ PROCESSING DATE ໃນໄຟລ໌ {path.name}")
    processing_date = proc_dates.iloc[0]
    logger.info(f"  Processing date: {processing_date}")

    def mode_or_first(series: pd.Series):
        m = series.mode()
        return m.iloc[0] if not m.empty else series.iloc[0]

    contract_branch_n = df.groupby("CONTRACT")["BRANCH"].nunique()
    multi_branch = contract_branch_n[contract_branch_n > 1].index.tolist()
    if multi_branch:
        logger.warning(
            f"  {len(multi_branch)} CONTRACT ມີຫຼາຍ BRANCH: {multi_branch[:5]}"
            + (" ..." if len(multi_branch) > 5 else "")
        )

    contract_currency_n = df.groupby("CONTRACT")["CURRENCY"].nunique()
    multi_currency = contract_currency_n[contract_currency_n > 1].index.tolist()
    if multi_currency:
        logger.warning(
            f"  {len(multi_currency)} CONTRACT ມີຫຼາຍ CURRENCY: {multi_currency[:5]}"
            + (" ..." if len(multi_currency) > 5 else "")
        )

    ldb_count = int(df["CONTRACT"].str.startswith("LDB").sum())
    if ldb_count:
        logger.info(f"  {ldb_count} ແຖວ LDB**** (ບັນຊີລະບົບ) ຈະຖືກ group+sum")

    grouped = (
        df.groupby("CONTRACT")
        .agg(
            BAL=("CONTRACT BAL", "sum"),
            LAKBAL=("LOCAL CURRENCY BAL", "sum"),
            BRANCH=("BRANCH", mode_or_first),
            CURRENCY=("CURRENCY", mode_or_first),
            CUSTOMER=("CUSTOMER", mode_or_first),
        )
        .reset_index()
    )

    logger.info(f"  Grouped to {len(grouped):,} unique contracts")

    return grouped, total_lak, processing_date
