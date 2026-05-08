from flask import Flask, request, jsonify, render_template_string
import time
import random
import yaml
import os
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# static information as metric
metrics.info('app_info', 'Application info', version='1.0.3')

@app.route('/')
def main():
    return "Python App with Monitoring - Home"

@app.route('/health')
def health():
    return jsonify({"status": "UP"}), 200

@app.route('/heavy-work')
def heavy_work():
    # Simulate CPU intensive work for HPA testing
    start_time = time.time()
    count = 0
    # Increase this number to generate more load
    limit = random.randint(1000000, 5000000)
    for i in range(limit):
        count += i
    end_time = time.time()
    return jsonify({
        "message": "Finished heavy work",
        "iterations": limit,
        "duration": end_time - start_time
    })

# --- Custom Alert Rule API and UI ---
ALERTS_FILE = 'monitoring/custom_alerts.yaml'

@app.route('/alerts', methods=['GET'])
def alerts_ui():
    # Simple HTML form for alert rule creation
    html = '''
    <h2>Create Custom Prometheus Alert Rule</h2>
    <form method="post" action="/api/alerts">
      <label>Alert Name: <input name="alert" required></label><br>
      <label>Expression: <input name="expr" required></label><br>
      <label>For (e.g. 1m): <input name="for" value="1m"></label><br>
      <label>Severity: <input name="severity" value="warning"></label><br>
      <label>Summary: <input name="summary" value="Custom alert"></label><br>
      <button type="submit">Create Alert</button>
    </form>
    <p>POST to <code>/api/alerts</code> with JSON or form data:<br>
    <pre>{"alert": "HighCPU", "expr": "sum(rate(cpu_usage[5m])) > 0.8", "for": "1m", "severity": "warning", "summary": "High CPU usage"}</pre></p>
    '''
    return render_template_string(html)

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    # Accept JSON or form data
    data = request.get_json() if request.is_json else request.form
    alert = data.get('alert')
    expr = data.get('expr')
    duration = data.get('for', '1m')
    severity = data.get('severity', 'warning')
    summary = data.get('summary', 'Custom alert')
    # Validation: required fields, type, and non-empty string
    if not isinstance(alert, str) or not isinstance(expr, str) or not alert.strip() or not expr.strip():
        return jsonify({"error": "'alert' and 'expr' are required non-empty strings"}), 400
    # Load existing alerts
    if not os.path.exists(ALERTS_FILE):
        alert_data = {"groups": [{"name": "custom-alerts", "rules": []}]}
    else:
        with open(ALERTS_FILE, 'r') as f:
            alert_data = yaml.safe_load(f) or {"groups": [{"name": "custom-alerts", "rules": []}]}
    # Find or create group
    group = next((g for g in alert_data['groups'] if g['name'] == 'custom-alerts'), None)
    if not group:
        group = {"name": "custom-alerts", "rules": []}
        alert_data['groups'].append(group)
    # Check for duplicate alert name
    if any(r.get('alert') == alert for r in group['rules']):
        return jsonify({"error": f"Alert rule with name '{alert}' already exists"}), 400
    # Add new rule
    rule = {
        "alert": alert,
        "expr": expr,
        "for": duration,
        "labels": {"severity": severity},
        "annotations": {"summary": summary}
    }
    group['rules'].append(rule)
    # Save back
    with open(ALERTS_FILE, 'w') as f:
        yaml.dump(alert_data, f)

    # Trigger Prometheus reload
    import requests
    PROM_URL = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
    reload_status = 'not attempted'
    import logging
    try:
        resp = requests.post(f'{PROM_URL}/-/reload', timeout=3)
        if resp.status_code == 200:
            reload_status = 'success'
        else:
            reload_status = f'failed: HTTP {resp.status_code}'
            logging.error(f'Prometheus reload failed: HTTP {resp.status_code} - {resp.text}')
    except Exception as e:
        reload_status = f'error: {e}'
        logging.exception(f'Prometheus reload error: {e}')

    return jsonify({"status": "ok", "rule": rule, "prometheus_reload": reload_status}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
