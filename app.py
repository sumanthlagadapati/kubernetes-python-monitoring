from flask import Flask, request, jsonify
import time
import random
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
