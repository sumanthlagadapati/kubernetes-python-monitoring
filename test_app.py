import os
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock
from app import app, ALERTS_FILE

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def temp_alerts_file(monkeypatch):
    # Use a temp file for alerts
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        monkeypatch.setattr('app.ALERTS_FILE', tf.name)
        yield tf.name
    os.remove(tf.name)

def test_create_alert_success(client, temp_alerts_file):
    alert_data = {
        "alert": "TestAlert",
        "expr": "up == 0",
        "for": "2m",
        "severity": "critical",
        "summary": "Test alert summary"
    }
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        resp = client.post('/api/alerts', json=alert_data)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['rule']['alert'] == 'TestAlert'
        assert data['prometheus_reload'] == 'success'
        # Check alert file content
        with open(temp_alerts_file) as f:
            alerts = yaml.safe_load(f)
            rules = alerts['groups'][0]['rules']
            assert any(r['alert'] == 'TestAlert' for r in rules)

def test_create_alert_reload_failure(client, temp_alerts_file):
    alert_data = {
        "alert": "FailReload",
        "expr": "up == 0"
    }
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = 'Internal Error'
        resp = client.post('/api/alerts', json=alert_data)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['prometheus_reload'].startswith('failed: HTTP 500')

def test_create_alert_reload_exception(client, temp_alerts_file):
    alert_data = {
        "alert": "ExceptionReload",
        "expr": "up == 0"
    }
    with patch('requests.post', side_effect=Exception('Connection error')):
        resp = client.post('/api/alerts', json=alert_data)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['prometheus_reload'].startswith('error:')

def test_create_alert_missing_fields(client):
    # Missing 'expr'
    resp = client.post('/api/alerts', json={"alert": "NoExpr"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data
    # Missing 'alert'
    resp = client.post('/api/alerts', json={"expr": "up == 0"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data

def test_create_alert_empty_required_fields(client):
    # Empty 'alert'
    resp = client.post('/api/alerts', json={"alert": "", "expr": "up == 0"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data
    # Empty 'expr'
    resp = client.post('/api/alerts', json={"alert": "EmptyExpr", "expr": ""})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data

def test_create_alert_invalid_types(client):
    # Non-string 'alert'
    resp = client.post('/api/alerts', json={"alert": 123, "expr": "up == 0"})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data
    # Non-string 'expr'
    resp = client.post('/api/alerts', json={"alert": "InvalidExprType", "expr": 123})
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'error' in data

def test_duplicate_alert_rule_name(client, temp_alerts_file):
    alert_data = {"alert": "DupAlert", "expr": "up == 0"}
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        # First creation should succeed
        resp1 = client.post('/api/alerts', json=alert_data)
        assert resp1.status_code == 201
        # Second creation with same name should fail
        resp2 = client.post('/api/alerts', json=alert_data)
        assert resp2.status_code == 400
        data = resp2.get_json()
        assert 'already exists' in data.get('error', '')
