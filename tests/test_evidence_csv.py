"""Regression checks for the user-supplied evidence used in chapters 6 and 7."""
import os
os.environ['AURA_DEMO']='1'
from fastapi.testclient import TestClient
from api import app


def test_evidence_sources_and_metadata():
    response = TestClient(app).get('/api/evaluation')
    assert response.status_code == 200
    data = response.json()
    assert data['baseline_source'] == data['fairness_source'] == 'csv'
    assert data['metadata_v1_source'] == data['metadata_thin_source'] == 'json'
    assert data['so_tinh']['n_features_thick'] == 188
    assert data['so_tinh']['n_features_thin'] == 86
    assert abs(data['so_tinh']['p99_ms']-102.00492918) < 1e-6
    # V2 metadata has no AUC; hiển thị giá trị tham chiếu 0,7704 theo báo cáo Phase 2
    # (yêu cầu chỉnh UI 02/11/2026: thẻ AUC Thin-file hiển thị 0,77 – 2 chữ số thập phân).
    assert data['so_tinh']['auc_thin'] == 0.7704


def test_baselines_means_from_40_runs():
    data = TestClient(app).get('/api/evaluation').json()
    assert data['baseline_runs'] == 40
    assert data['baseline_seeds_per_fund'] == {'1.5': 20, '2.0': 20}
    lookup = {(r['quy_ty'],r['phuong_an'][:2]):r for r in data['baseline']}
    assert abs(lookup[(1.5,'B3')]['loi_nhuan_that_trieu'] - 41.507375) < 1e-5
    assert abs(lookup[(2.0,'B3')]['loi_nhuan_that_trieu'] - 42.481) < 1e-5


def test_fairness_correct_group_labels_and_missing_coverage():
    data = TestClient(app).get('/api/evaluation').json()
    assert len(data['fairness']) == 19
    assert data['fairness_coverage']['Giới tính'] == 977
    assert data['fairness_coverage']['Học vấn'] == 29974
    ages = [r for r in data['fairness'] if r['nhom_loai'] == 'Nhóm tuổi']
    assert len(ages) == 5
    first = next(r for r in ages if r['nhom'] == '<25')
    assert abs(first['false_reject'] - .45520361991) < 1e-6
    assert abs(first['high'] - .4870759289176) < 1e-6
