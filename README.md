# ລະບົບສົມທຽບເງິນຝາກ CRB — CRB Deposit Comparison

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/lormany59-byte/crb-compare)

ເຄື່ອງມື web ສຳລັບ **ປຽບທຽບ (compare) ໄຟລ໌ສົ່ງອອກ CRB 2 ໄຟລ໌** ແລ້ວສ້າງເປັນ
ໄຟລ໌ Excel ລາຍງານທີ່ຈັດຮູບແບບໃຫ້ສວຍງາມໂດຍອັດຕະໂນມັດ. ພຽງແຕ່ລາກ (drag & drop)
ໄຟລ໌ Excel 2 ໄຟລ໌ເຂົ້າໄປ ກໍໄດ້ໄຟລ໌ລາຍງານປຽບທຽບກັບຄືນມາ.

> A small Flask web app: drop in two CRB export files (`.xlsx`) and get back a
> styled comparison report. Old/new files are auto-detected from the processing
> date — you don't need to label them.

---

## ✨ ຄຸນສົມບັດ (Features)

- 🖱️ **Drag & drop** ໄຟລ໌ Excel 2 ໄຟລ໌ ຜ່ານ web ໂດຍກົງ
- 🔁 **Auto-detect** ໄຟລ໌ເກົ່າ/ໃໝ່ ຈາກວັນທີ (PROCESSING DATE / ຊື່ໄຟລ໌)
- 🏦 ແຍກຕາມ **ສາຂາ / ໜ່ວຍບໍລິການ** ແລະ ຕາມ **ສະກຸນເງິນ** (LAK, USD, THB, CNY)
- ⚙️ ປັບ **threshold** ໄດ້ຕໍ່ຄັ້ງ ໂດຍບໍ່ຕ້ອງແກ້ໂຄ້ດ (ກຳນົດຄ່າເລີ່ມຕົ້ນໃນ `config.yaml`)
- 📊 ໄດ້ໄຟລ໌ Excel ທີ່ຈັດຮູບແບບແລ້ວ ພ້ອມໃຊ້

---

## 🚀 ການຕິດຕັ້ງ ແລະ ໃຊ້ງານ (Local)

ຕ້ອງມີ **Python 3.10+**.

```bash
# 1. clone repo
git clone https://github.com/lormany59-byte/crb-compare.git
cd crb-compare

# 2. (ແນະນຳ) ສ້າງ virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. ຕິດຕັ້ງ dependencies
pip install -r requirements.txt

# 4. ເປີດ server
python app.py
```

ຈາກນັ້ນເປີດ browser ໄປທີ່ <http://127.0.0.1:5000>, ລາກໄຟລ໌ CRB 2 ໄຟລ໌ເຂົ້າໄປ
ແລ້ວກົດ **ປະມວນຜົນ ແລະ ດາວໂຫຼດ**.

---

## ☁️ Deploy ຂຶ້ນ web (ໃຫ້ຄົນອື່ນເຂົ້າໃຊ້ໄດ້)

repo ນີ້ມີ [`render.yaml`](render.yaml) ຢູ່ແລ້ວ — deploy ຟຣີຜ່ານ
[Render](https://render.com) ໄດ້ເລີຍ:

1. push code ຂຶ້ນ GitHub (ເຮັດແລ້ວ).
2. ເຂົ້າ Render → **New → Blueprint** → ເລືອກ repo ນີ້.
3. Render ຈະອ່ານ `render.yaml` ແລະ ສ້າງ service `crb-compare` ໃຫ້ອັດຕະໂນມັດ.

ຫຼື platform ໃດກໍໄດ້ທີ່ຮອງຮັບ `app.py` + `requirements.txt` ທີ່ root
(ເຊັ່ນ `gunicorn app:app`).

---

## ⚙️ ການຕັ້ງຄ່າ (Configuration)

ແກ້ [`crb_compare/config.yaml`](crb_compare/config.yaml) ໂດຍບໍ່ຕ້ອງແຕະໂຄ້ດ:

| ຄ່າ | ຄວາມໝາຍ |
| --- | --- |
| `branch_map` | map ລະຫັດສາຂາ → ຊື່ສາຂາ/ໜ່ວຍບໍລິການ |
| `thresholds` | ຖ້າ `\|diff\|` ≥ ຄ່ານີ້ ຈຶ່ງນັບເປັນ "ລາຍເຄື່ອນໄຫວໃຫຍ່" (ຕໍ່ສະກຸນເງິນ) |
| `currency_order` | ລຳດັບການສະແດງສະກຸນເງິນ |
| `output_raw_report` | ເປີດ/ປິດ sheet "Report" (ສຳເນົາວິທີເກົ່າ) |

---

## 📁 ໂຄງສ້າງ project (Project structure)

```
crb-compare/
├── app.py              # entry point ທີ່ root (re-export Flask app)
├── main.py             # entry point ສຳຮອງ
├── requirements.txt
├── render.yaml         # config ສຳລັບ deploy ຂຶ້ນ Render
└── crb_compare/
    ├── app.py          # Flask web app
    ├── compare.py      # logic ປຽບທຽບ + ສະຖິຕິ
    ├── reader.py       # ອ່ານ/parse ໄຟລ໌ CRB
    ├── excel_writer.py # ສ້າງ Excel ທີ່ຈັດຮູບແບບແລ້ວ
    ├── config.yaml     # ການຕັ້ງຄ່າ
    └── templates/
        └── index.html  # ໜ້າ web
```

---

## 🧪 Tests

```bash
pip install -r requirements.txt
pytest
```

---

## 📄 License

[MIT](LICENSE) — ໃຊ້, ແກ້ໄຂ, ແລະ ແຈກຈ່າຍໄດ້ຢ່າງເສລີ.
