"""Tải mô hình thật + CSDL từ Google Drive về máy để chạy api.py với lõi thật.
Dùng:  python tai_mo_hinh.py "<link thư mục Drive đã share Anyone-with-link>"  [thư_mục_đích]
Thư mục Drive cần chứa: fpd_model_v1/ , aura_bnpl.db , baseline_comparison.csv , fairness.csv (tuỳ chọn)
Sau khi tải xong, chạy:  AURA_BASE=./du_lieu/ uvicorn api:app --port 8000   (Windows PowerShell: $env:AURA_BASE="./du_lieu/")
"""
import os, sys, subprocess
try: import gdown
except ImportError: subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "gdown"]); import gdown
link = sys.argv[1] if len(sys.argv) > 1 else input("Dán link thư mục Drive: ").strip()
dest = (sys.argv[2] if len(sys.argv) > 2 else "du_lieu").rstrip("/\\") + "/"
os.makedirs(dest, exist_ok=True)
print(f"Tải về {dest} ...")
gdown.download_folder(url=link, output=dest, quiet=False, use_cookies=False, remaining_ok=True)
can = ["fpd_model_v1", "aura_bnpl.db"]
thieu = [c for c in can if not os.path.exists(dest + c)]
# gdown đôi khi tạo thêm 1 cấp thư mục trùng tên -> kéo lên
if thieu:
    for d in os.listdir(dest):
        p = dest + d
        if os.path.isdir(p) and all(os.path.exists(os.path.join(p, c)) for c in can):
            for f in os.listdir(p): os.replace(os.path.join(p, f), dest + f)
            os.rmdir(p); thieu = []; break
print("THIẾU:", thieu if thieu else "không – đủ file.")
print(f"\nChạy lõi thật:\n  Windows PowerShell:  $env:AURA_BASE=\"{os.path.abspath(dest)}\\\"; python -m uvicorn api:app --port 8000"
      f"\n  Mac/Linux:           AURA_BASE={os.path.abspath(dest)}/ uvicorn api:app --port 8000\n  Kiểm tra: http://localhost:8000/api/health  ->  \"demo\": false")
