import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

QBER_THRESHOLD = 0.11

def bb84_protocol(n_qubits=10, noise_prob=0.0, eve_prob=0.0):
    """
    Full BB84 protocol simulation.
    """
    effective_gate_noise = noise_prob
    effective_readout_noise = noise_prob + (eve_prob * 0.25)

    alice_bits = np.random.randint(2, size=n_qubits).astype(int)
    alice_bases = np.random.randint(2, size=n_qubits).astype(int)
    bob_bases = np.random.randint(2, size=n_qubits).astype(int)
    
    qc = QuantumCircuit(n_qubits, n_qubits)
    
    # Alice encodes
    for i in range(n_qubits):
        if alice_bits[i] == 1:
            qc.x(i)
        if alice_bases[i] == 1:
            qc.h(i)
    qc.barrier()
  
    # Bob measures
    for i in range(n_qubits):
        if bob_bases[i] == 1:
            qc.h(i)
    qc.barrier()
    qc.measure(range(n_qubits), range(n_qubits))

    simulator = AerSimulator()
    if effective_gate_noise > 0 or effective_readout_noise > 0:
        noise_model = NoiseModel()
        if effective_gate_noise > 0:
            depol_error = depolarizing_error(effective_gate_noise, 1)
            noise_model.add_all_qubit_quantum_error(depol_error, ['h', 'x'])
        if effective_readout_noise > 0:
            readout_probs = [[1 - effective_readout_noise, effective_readout_noise], 
                           [effective_readout_noise, 1 - effective_readout_noise]]
            readout_error = ReadoutError(readout_probs)
            noise_model.add_all_qubit_readout_error(readout_error)
        simulator = AerSimulator(noise_model=noise_model)
    
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    measured_str = max(counts, key=counts.get)
    measured_bits = [int(bit) for bit in reversed(measured_str)]

    sifted_indices = [i for i in range(n_qubits) if alice_bases[i] == bob_bases[i]]
    alice_sifted = [int(alice_bits[i]) for i in sifted_indices]
    bob_sifted = [measured_bits[i] for i in sifted_indices]
    sifted_length = len(sifted_indices)

    if sifted_length == 0:
        return {
            'qber': 1.0, 
            'sifted_length': 0, 
            'key_length': 0, 
            'detected_eve': True,
            'alice_sifted_key': [], 
            'bob_sifted_key': [], 
            'alice_final_key': [], 
            'bob_final_key': []
        }
    
    est_size = max(1, sifted_length // 2)
    est_indices = np.random.choice(range(sifted_length), est_size, replace=False)
    errors = sum(alice_sifted[j] != bob_sifted[j] for j in est_indices)
    qber = errors / est_size

    total_errors = sum(alice_sifted[j] != bob_sifted[j] for j in range(sifted_length))
    detected_eve = (qber > QBER_THRESHOLD) or (total_errors > 0)

    key_indices = [j for j in range(sifted_length) if j not in set(est_indices)]
    matching_key_indices = [j for j in key_indices if alice_sifted[j] == bob_sifted[j]]
    alice_final_key = [int(alice_sifted[j]) for j in matching_key_indices]
    bob_final_key = [bob_sifted[j] for j in matching_key_indices]
    key_length = len(matching_key_indices)
    
    return {
        'qber': qber,
        'sifted_length': sifted_length,
        'key_length': key_length,
        'detected_eve': detected_eve,
        'alice_sifted_key': alice_sifted,
        'bob_sifted_key': bob_sifted,
        'alice_final_key': alice_final_key,
        'bob_final_key': bob_final_key
    }

def collect_metrics_for_plotting(n_runs=10, n_qubits=10):
    """Collects average QBER and detection rate across varying noise and Eve levels."""
    
    # 1. Quantum Noise (Eve_prob = 0)
    noise_levels = np.linspace(0, 0.15, 7)
    results_noise = {'x': noise_levels, 'qber': []}
    for noise in noise_levels:
        qbers = []
        for _ in range(n_runs):
            m = bb84_protocol(n_qubits=n_qubits, noise_prob=noise, eve_prob=0.0)
            qbers.append(m['qber'])
        results_noise['qber'].append(np.mean(qbers))
        
    # 2. Eavesdrop Attack (Noise_prob = 0)
    eve_levels = np.linspace(0, 1.0, 7)
    results_eve = {'x': eve_levels, 'qber': [], 'detection_rate': []}
    for eve_p in eve_levels:
        qbers, detections = [], []
        for _ in range(n_runs):
            m = bb84_protocol(n_qubits=n_qubits, noise_prob=0.0, eve_prob=eve_p)
            qbers.append(m['qber'])
            detections.append(1 if m['detected_eve'] else 0)
        results_eve['qber'].append(np.mean(qbers))
        results_eve['detection_rate'].append(np.mean(detections))
    
    return results_noise, results_eve