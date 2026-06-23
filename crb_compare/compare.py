"""Steps 2-4: determine base/compare direction, outer join, diff, classify, filter."""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def determine_base_compare(
    df1: pd.DataFrame,
    date1: str,
    df2: pd.DataFrame,
    date2: str,
    lak1: float,
    lak2: float,
):
    """Older PROCESSING DATE = base, newer = compare.

    Returns (base_df, base_date, base_lak, compare_df, compare_date, compare_lak).
    """
    if date1 == date2:
        raise ValueError(
            f"ໄຟລ໌ທັງສອງມີ PROCESSING DATE ດຽວກັນ ({date1}). "
            "ກະລຸນາໂຍນໄຟລ໌ຈາກ 2 ວັນທີ່ແຕກຕ່າງກັນ."
        )
    if date1 < date2:
        return df1, date1, lak1, df2, date2, lak2
    return df2, date2, lak2, df1, date1, lak1


def compute_diff(
    base: pd.DataFrame,
    compare: pd.DataFrame,
    branch_map: dict,
    thresholds: dict,
    currency_order: list,
):
    """Outer-merge base/compare, compute diff, classify, map branch, flag significant.

    Returns (merged_df, stats_dict).
    """
    merged = pd.merge(
        base.rename(columns={"BAL": "base_bal", "LAKBAL": "base_lakbal"}),
        compare.rename(columns={"BAL": "compare_bal", "LAKBAL": "compare_lakbal"}),
        on="CONTRACT",
        how="outer",
        suffixes=("_base", "_compare"),
    )

    merged["base_bal"] = merged["base_bal"].fillna(0.0)
    merged["compare_bal"] = merged["compare_bal"].fillna(0.0)
    merged["base_lakbal"] = merged["base_lakbal"].fillna(0.0)
    merged["compare_lakbal"] = merged["compare_lakbal"].fillna(0.0)

    for col in ["BRANCH", "CURRENCY", "CUSTOMER"]:
        compare_col, base_col = f"{col}_compare", f"{col}_base"
        if compare_col in merged.columns and base_col in merged.columns:
            merged[col] = merged[compare_col].where(
                merged[compare_col].notna() & (merged[compare_col] != ""),
                merged[base_col],
            )
        elif compare_col in merged.columns:
            merged[col] = merged[compare_col]
        elif base_col in merged.columns:
            merged[col] = merged[base_col]
        merged[col] = merged[col].fillna("").astype(str)

    merged["diff"] = merged["compare_bal"] - merged["base_bal"]
    merged["diff_lak"] = merged["compare_lakbal"] - merged["base_lakbal"]

    merged["change_type"] = "ເທົ່າ"
    merged.loc[merged["diff"] > 0, "change_type"] = "ເພີ່ມ"
    merged.loc[merged["diff"] < 0, "change_type"] = "ຫຼຸດ"

    merged["is_new"] = (merged["base_bal"] == 0) & (merged["compare_bal"] != 0)
    merged["is_closed"] = (merged["base_bal"] != 0) & (merged["compare_bal"] == 0)

    unknown_branches = set()

    def map_branch(code):
        if code in branch_map:
            return branch_map[code]
        if code:
            unknown_branches.add(code)
        return code

    merged["BranchName"] = merged["BRANCH"].apply(map_branch)
    if unknown_branches:
        logger.warning(
            f"ລະຫັດສາຂາທີ່ບໍ່ມີໃນ config (ໃຊ້ລະຫັດດິບ + flag): {sorted(unknown_branches)}"
        )

    unknown_currencies = set()

    def get_threshold(currency):
        if currency and currency not in thresholds:
            unknown_currencies.add(currency)
            return 0
        return thresholds.get(currency, 0)

    merged["threshold"] = merged["CURRENCY"].apply(get_threshold)
    merged["is_significant"] = merged["diff"].abs() >= merged["threshold"]

    if unknown_currencies:
        logger.warning(
            f"ສະກຸນເງິນທີ່ບໍ່ມີ threshold ໃນ config (default=0, ນັບລວມໝົດ): "
            f"{sorted(unknown_currencies)}"
        )

    stats = {
        "total": int(len(merged)),
        "increase": int((merged["change_type"] == "ເພີ່ມ").sum()),
        "decrease": int((merged["change_type"] == "ຫຼຸດ").sum()),
        "equal": int((merged["change_type"] == "ເທົ່າ").sum()),
        "new": int(merged["is_new"].sum()),
        "closed": int(merged["is_closed"].sum()),
        "significant": int(merged["is_significant"].sum()),
    }

    logger.info(f"Comparison: {stats['total']:,} ບັນຊີລວມ")
    logger.info(
        f"  ເພີ່ມ: {stats['increase']:,}  ຫຼຸດ: {stats['decrease']:,}  ເທົ່າ: {stats['equal']:,}"
    )
    logger.info(f"  ເປີດໃໝ່: {stats['new']:,}  ປິດ: {stats['closed']:,}")
    logger.info(f"  ລາຍເຄື່ອນໄຫວໃຫຍ່ (|diff| >= threshold): {stats['significant']:,}")

    return merged, stats


def summary_by_branch_currency(merged: pd.DataFrame, currency_order: list) -> pd.DataFrame:
    """groupby Branch x CURRENCY -> sum(base_bal), sum(compare_bal), sum(diff), count."""
    summary = (
        merged.groupby(["BranchName", "CURRENCY"])
        .agg(
            base_sum=("base_bal", "sum"),
            compare_sum=("compare_bal", "sum"),
            count=("CONTRACT", "count"),
        )
        .reset_index()
    )
    summary["diff"] = summary["compare_sum"] - summary["base_sum"]

    cat = pd.Categorical(summary["CURRENCY"], categories=currency_order, ordered=True)
    summary["_ord"] = cat
    summary = summary.sort_values(["_ord", "BranchName"]).drop(columns=["_ord"])
    return summary
