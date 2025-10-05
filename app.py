from flask import Flask, render_template, request, jsonify
import numpy as np
from bb84_protocol import bb84_protocol, collect_metrics_for_plotting
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        data = request.get_json()
        n_qubits = int(data.get('n_qubits', 10))
        noise_prob = float(data.get('noise_prob', 0.0))
        eve_prob = float(data.get('eve_prob', 0.0))
        
        # Run simulation
        result = bb84_protocol(n_qubits=n_qubits, noise_prob=noise_prob, eve_prob=eve_prob)
        
        # Convert numpy types to native Python types for JSON serialization
        result_json = {
            'qber': float(result['qber']),
            'sifted_length': int(result['sifted_length']),
            'key_length': int(result['key_length']),
            'detected_eve': bool(result['detected_eve']),
            'alice_sifted_key': [int(x) for x in result['alice_sifted_key']],
            'bob_sifted_key': [int(x) for x in result['bob_sifted_key']],
            'alice_final_key': [int(x) for x in result['alice_final_key']],
            'bob_final_key': [int(x) for x in result['bob_final_key']]
        }
        
        return jsonify(result_json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        n_runs = int(data.get('n_runs', 10))
        n_qubits = int(data.get('n_qubits', 25))
        
        # Collect metrics for plotting
        results_noise, results_eve = collect_metrics_for_plotting(n_runs=n_runs, n_qubits=n_qubits)
        
        # Convert to JSON-serializable format
        analysis_data = {
            'noise': {
                'x': [float(x) * 100 for x in results_noise['x']],
                'qber': [float(q) for q in results_noise['qber']]
            },
            'eve': {
                'x': [float(x) * 100 for x in results_eve['x']],
                'qber': [float(q) for q in results_eve['qber']],
                'detection_rate': [float(d) for d in results_eve['detection_rate']]
            }
        }
        
        return jsonify(analysis_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)