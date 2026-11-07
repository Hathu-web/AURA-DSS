"""Integration smoke tests: always run against simulated data, never require real model files."""
import os
os.environ["AURA_DEMO"] = "1"

from fastapi.testclient import TestClient
from api import app, sql_an_toan


def test_health_and_summary():
    with TestClient(app) as c:
        health = c.get('/api/health')
        assert health.status_code == 200 and health.json()['demo'] is True
        summary = c.get('/api/summary')
        assert summary.status_code == 200
        assert summary.json()['kpi']['so_giao_dich'] == 6000


def test_out_of_range_and_invalid_dates():
    with TestClient(app) as c:
        r = c.get('/api/summary?d_from=2027-01-01&d_to=2027-01-10')
        assert r.status_code == 200 and r.json()['kpi']['so_giao_dich'] == 0
        assert c.get('/api/summary?d_from=2027-02-01&d_to=2027-01-01').status_code == 422


def test_search_uses_literal_matching_and_hides_labels():
    with TestClient(app) as c:
        r = c.get('/api/transactions?q=\\&limit=10')
        assert r.status_code == 200 and r.json()['total'] == 0
        rows = c.get('/api/transactions?limit=2').json()['rows']
        assert rows and all('target_default' not in row for row in rows)


def test_score_and_optimize():
    with TestClient(app) as c:
        r = c.get('/api/score/243023')
        assert r.status_code == 200 and r.json()['tier_code'] == 'HIGH'
        assert c.post('/api/optimize', json={'liquidity': -3}).status_code == 422
        r = c.post('/api/optimize', json={'n': 100})
        assert r.status_code == 200
        assert r.json()['kq']['solver'] == 'DEMO'
        rid = r.json()['run_id']
        assert c.post('/api/log', json={'run_id': rid}).status_code == 200
        assert c.post('/api/log', json={'run_id': rid}).status_code == 404


def test_assistant_and_upload_errors():
    with TestClient(app) as c:
        r = c.post('/api/ask', json={'question': 'Có bao nhiêu giao dịch?'})
        assert r.status_code == 200 and r.json()['offline'] is True
        assert c.post('/api/upload?kind=applications', files={'file': ('bad.txt', b'hello')}).status_code == 400
        assert c.post('/api/upload?kind=applications', files={'file': ('empty.csv', b'x,y\n')}).status_code == 400


def test_sql_only_read_limited():
    assert sql_an_toan('SELECT customer_id FROM DIM_CUSTOMER') == 'SELECT customer_id FROM DIM_CUSTOMER LIMIT 200'
    assert sql_an_toan('DELETE FROM DIM_CUSTOMER') is None
    assert sql_an_toan('SELECT * FROM DIM_CUSTOMER LIMIT 5000') is None
    assert sql_an_toan(None) is None
