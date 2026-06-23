#!/usr/bin/env python3
"""CRB Deposit Comparison System — CLI entry point.

Usage:
    python crb_compare.py --base CRB_old.xlsx --compare CRB_new.xlsx --out report.xlsx
    python crb_compare.py CRB_a.xlsx CRB_b.xlsx --out report.xlsx   # auto-detect base/compare
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

from compare import compute_diff, determine_base_compare
from excel_writer import create_comparison_workbook, write_excel
from reader import read_crb
from reconcile import reconcile

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "branch_map": {},
    "thresholds": {"LAK": 100000000, "USD": 10000, "THB": 500000, "CNY": 1000},
    "currency_order": ["LAK", "USD", "THB", "CNY"],
    "output_raw_report": False,
}


def load_config(path) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path:
        with open(path, encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        cfg.update(user_cfg)
    return cfg


def run(file_a: str, file_b: str, out_path: str, cfg: dict) -> dict:
    """Run the full pipeline; returns stats dict. Raises on reconcile/data errors."""
    df1, lak1, date1 = read_crb(file_a)
    df2, lak2, date2 = read_crb(file_b)

    reconcile(df1["LAKBAL"].sum(), lak1, Path(file_a).name)
    reconcile(df2["LAKBAL"].sum(), lak2, Path(file_b).name)

    base_df, base_date, base_lak, compare_df, compare_date, compare_lak = (
        determine_base_compare(df1, date1, df2, date2, lak1, lak2)
    )
    logger.info(f"Base: {base_date}, Compare: {compare_date}")

    merged, stats = compute_diff(
        base_df, compare_df, cfg["branch_map"], cfg["thresholds"], cfg["currency_order"]
    )

    wb = create_comparison_workbook(
        merged=merged,
        stats=stats,
        base_date=base_date,
        compare_date=compare_date,
        base_lak=base_lak,
        compare_lak=compare_lak,
        branch_map=cfg["branch_map"],
        thresholds=cfg["thresholds"],
        currency_order=cfg["currency_order"],
        output_raw_report=cfg.get("output_raw_report", False),
    )
    write_excel(wb, out_path)
    return stats


def main():
    parser = argparse.ArgumentParser(description="CRB Deposit Comparison")
    parser.add_argument("--base", help="Base CRB file (older date)")
    parser.add_argument("--compare", help="Compare CRB file (newer date)")
    parser.add_argument("--out", default="crb_report.xlsx", help="Output Excel file")
    parser.add_argument("--config", help="Config YAML file")
    parser.add_argument("files", nargs="*", help="Two CRB files (auto-detect base/compare)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.base and args.compare:
        file_a, file_b = args.base, args.compare
    elif len(args.files) == 2:
        file_a, file_b = args.files
    else:
        parser.error("ໃຫ້ໃສ່ --base ແລະ --compare, ຫຼື 2 ໄຟລ໌ແບບ positional")
        return

    try:
        stats = run(file_a, file_b, args.out, cfg)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info(f"\nສຳເລັດ! Output: {args.out}")
    logger.info(
        f"ບັນຊີ: {stats['total']:,} ລວມ, {stats['increase']:,} ເພີ່ມ, "
        f"{stats['decrease']:,} ຫຼຸດ, {stats['equal']:,} ເທົ່າ"
    )
    logger.info(
        f"ເປີດໃໝ່: {stats['new']:,}, ປິດ: {stats['closed']:,}, "
        f"ລາຍເຄື່ອນໄຫວໃຫຍ່: {stats['significant']:,}"
    )


if __name__ == "__main__":
    main()
