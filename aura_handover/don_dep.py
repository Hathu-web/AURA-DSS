"""Dọn thư mục bàn giao: xoá node_modules, __pycache__, file trung gian. Chạy: python don_dep.py"""
import shutil, os, glob
XOA_DIR = ["web/node_modules", "__pycache__", "web/.vite"]
XOA_FILE = ["hinh/flow.dot", "hinh/flow2.dot"]
for d in XOA_DIR:
    if os.path.isdir(d): shutil.rmtree(d); print("xoá", d)
for f in XOA_FILE + glob.glob("**/*.pyc", recursive=True):
    if os.path.exists(f): os.remove(f); print("xoá", f)
print("Xong. Thư mục cần giữ: api.py model.py features.py llm.py demo_core.py web_build/ web/ requirements.txt HUONG_DAN_CHAY.md hinh/")
