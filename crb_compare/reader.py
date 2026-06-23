"""Step 1: read, clean, and group a single CRB export file."""

import logging
import re
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


def extract_date_from_filename(filename) -> str:
    """Pull YYYYMMDD out of a CRB filename like CRB_2026-05-18_09_49_10.xlsx.

    The PROCESSING DATE column inside the file is a T-1 extract (it reflects
    the prior business day's closing balances, generated the next morning),
    so the calendar date the report should show/order by comes from the
    filename instead.
    """
    name = Path(filename).name
    match = re.search(r"(\d{4})[-_](\d{2})[-_](\d{2})", name)
    if not match:
        raise ValueError(f"ບໍ່ພົບວັນທີ່ໃນຊື່ໄຟລ໌ (ຄາດຫວັງ YYYY-MM-DD): {name}")
    return "".join(match.groups())


def read_crb(path) -> tuple[pd.DataFrame, str]:
    """Read and clean one CRB export file.

    Rows 1-5 are a summary/totals block and are never read — the real header
    is row 6 and data starts at row 7.

    Returns:
        grouped: one row per CONTRACT with BAL / LAKBAL / BRANCH / CURRENCY / CUSTOMER
        processing_date: YYYYMMDD string from the file's own PROCESSING DATE
            column (kept for diagnostics only — callers should use
            extract_date_from_filename for the date that drives the report)
    """
    path = Path(path)
    logger.info(f"Reading {path.name}...")

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

    raw_col = df["PROCESSING DATE"].dropna()
    if not raw_col.empty:
        raw_sample = raw_col.iloc[0]
        logger.info(
            f"  [DEBUG] PROCESSING DATE raw dtype={df['PROCESSING DATE'].dtype}, "
            f"sample value={raw_sample!r} (type={type(raw_sample).__name__})"
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

    return grouped, processing_date
