from flask import Flask, send_from_directory, jsonify
import threading
import subprocess
from pathlib import Path
import os

app = Flask(__name__)
_runner = None

def _run_pipeline():
    out_dir = Path('output')
    out_dir.mkdir(exist_ok=True)
    subprocess.run(['python', 'app.py'], check=False)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.post('/run')
def run_pipeline():
    global _runner
    if _runner and _runner.is_alive():
        return jsonify({'status': 'running'})
    _runner = threading.Thread(target=_run_pipeline, daemon=True)
    _runner.start()
    return jsonify({'status': 'started'})

@app.get('/logs')
def get_logs():
    log_path = Path('output/run.log')
    if log_path.exists():
        return log_path.read_text()
    return '', 204

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
