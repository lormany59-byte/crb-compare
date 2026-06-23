"""Flask web app — drag two CRB exports in, get the styled comparison Excel back."""

import logging
import traceback
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from flask import Flask, jsonify, render_template, request, send_file

from compare import compute_diff, determine_base_compare
from excel_writer import create_comparison_workbook
from reader import read_crb
from reconcile import reconcile

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config.yaml"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB, ~42k-row files


def load_config() -> dict:
    with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@app.route("/")
def index():
    cfg = load_config()
    return render_template("index.html", config=cfg)


@app.route("/process", methods=["POST"])
def process():
    file_a = request.files.get("file_a")
    file_b = request.files.get("file_b")

    if not file_a or not file_b:
        return jsonify({"error": "ກະລຸນາໂຍນ 2 ໄຟລ໌ CRB"}), 400

    cfg = load_config()

    # Optional per-request threshold overrides from the form
    thresholds = dict(cfg.get("thresholds", {}))
    for currency in list(thresholds.keys()):
        override = request.form.get(f"threshold_{currency}")
        if override:
            try:
                thresholds[currency] = float(override)
            except ValueError:
                pass
    cfg["thresholds"] = thresholds

    tmp_paths = []
    try:
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_a:
            file_a.save(tmp_a.name)
            tmp_paths.append(tmp_a.name)
        with NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_b:
            file_b.save(tmp_b.name)
            tmp_paths.append(tmp_b.name)

        df1, lak1, date1 = read_crb(tmp_paths[0])
        df2, lak2, date2 = read_crb(tmp_paths[1])

        reconcile(df1["LAKBAL"].sum(), lak1, file_a.filename)
        reconcile(df2["LAKBAL"].sum(), lak2, file_b.filename)

        base_df, base_date, base_lak, compare_df, compare_date, compare_lak = (
            determine_base_compare(df1, date1, df2, date2, lak1, lak2)
        )

        merged, stats = compute_diff(
            base_df, compare_df, cfg["branch_map"], thresholds, cfg["currency_order"]
        )

        wb = create_comparison_workbook(
            merged=merged,
            stats=stats,
            base_date=base_date,
            compare_date=compare_date,
            base_lak=base_lak,
            compare_lak=compare_lak,
            branch_map=cfg["branch_map"],
            thresholds=thresholds,
            currency_order=cfg["currency_order"],
            output_raw_report=cfg.get("output_raw_report", False),
        )

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        out_name = f"crb_report_{base_date}_{compare_date}.xlsx"
        return send_file(
            buf,
            as_attachment=True,
            download_name=out_name,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        logger.error(str(e))
        return jsonify({"error": str(e)}), 400
    except Exception:
        logger.error(traceback.format_exc())
        return jsonify({"error": "ເກີດຂໍ້ຜິດພາດທີ່ບໍ່ໄດ້ຄາດໝາຍ — ກວດ log ຂອງ server"}), 500
    finally:
        for p in tmp_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
