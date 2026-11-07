"""Kiểm thử tích hợp Agentic RAG: luôn chạy với dữ liệu mô phỏng, không cần model thật."""
import os
os.environ["AURA_DEMO"] = "1"

from fastapi.testclient import TestClient
from api import app, AGENT
from agent_rag import phan_loi_y_dinh, nap_corpus, mask_pii_question


def test_corpus_da_nap():
    chunks = nap_corpus()
    assert len(chunks) >= 8, "Cần ít nhất 8 chunk trong rag_corpus/"
    assert all(c["title"] and c["text"] for c in chunks)
    hits = AGENT.index.search("AUC mô hình LightGBM thick thin là bao nhiêu", k=3)
    assert hits and "03_mo_hinh_diem_lightgbm" in hits[0]["id"]


def test_phan_loi_y_dinh():
    assert phan_loi_y_dinh("Khách 243023 có yếu tố nào làm tăng rủi ro?") == "ho_so"
    assert phan_loi_y_dinh("Chạy tối ưu vốn với trần rủi ro 3%") == "toi_uu"
    assert phan_loi_y_dinh("FR-03 quy định gì về phân tầng?") == "tai_lieu"
    assert phan_loi_y_dinh("Top 10 giao dịch rủi ro nhất") == "truy_van"
    assert phan_loi_y_dinh("Giá bitcoin hôm nay thế nào?") == "ngoai_pham_vi"


def test_mask_pii_trong_cau_hoi():
    assert "[EMAIL_ẨN]" in mask_pii_question("liên hệ test@gmail.com giúp tôi")
    assert "[ĐIỆN_THOẠI_ẨN]" in mask_pii_question("gọi số 0912345678")


def test_api_agent_ky_suatchat_doi():
    with TestClient(app) as c:
        r = c.post('/api/agent', json={'question': 'Tỷ lệ chọn và rủi ro dự báo trong kỳ này?'})
        assert r.status_code == 200
        d = r.json()
        assert d['intent'] in {'tong_hop', 'tai_lieu'}
        assert d['text'] and d['trace'] and d['trace'][0]['tool'] == 'phan_loi'
        assert all('ms' in s and 'trang_thai' in s for s in d['trace'])
        assert d['tong_ms'] >= 0


def test_api_agent_ho_so():
    with TestClient(app) as c:
        r = c.post('/api/agent', json={'question': 'Khách 243023 có yếu tố nào làm tăng điểm rủi ro?'})
        assert r.status_code == 200
        d = r.json()
        assert d['intent'] == 'ho_so'
        tools = [s['tool'] for s in d['trace']]
        assert 'score_customer' in tools and 'policy_rules' in tools
        assert d['text'] and '243023' in d['text']


def test_api_agent_ngoai_pham_vi_tu_choi():
    with TestClient(app) as c:
        r = c.post('/api/agent', json={'question': 'Cho mình xin giá bitcoin hôm nay'})
        assert r.status_code == 200
        d = r.json()
        assert d['intent'] == 'ngoai_pham_vi'
        assert 'ngoài phạm vi' in d['text'].lower()
        assert not any(s['tool'] == 'run_milp' for s in d['trace'])


def test_api_agent_milp_khong_tu_ghi():
    with TestClient(app) as c:
        r = c.post('/api/agent', json={'question': 'Tối ưu phân bổ vốn với quỹ 2 tỷ, trần rủi ro 4%'})
        assert r.status_code == 200
        d = r.json()
        assert d['intent'] == 'toi_uu' and d['run_id'] is None          # mặc định KHÔNG ghi
        r2 = c.post('/api/agent', json={'question': 'Tối ưu phân bổ vốn với quỹ 2 tỷ', 'confirm': True})
        assert r2.status_code == 200
        assert r2.json()['run_id'] is not None                          # confirm=True mới ghi batch
