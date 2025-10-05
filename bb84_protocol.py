import numpy as np
# All Qiskit imports are removed to satisfy Vercel's size limit.

QBER_THRESHOLD = 0.11

def bb84_protocol(n_qubits=10, noise_prob=0.0, eve_prob=0.0):
    """
    Full BB84 protocol simulation, implemented using only NumPy 
    and classical logic to meet Vercel size constraints.
    """
    # effective_gate_noise is ignored as all noise is modeled as readout/bit-flip.
    effective_readout_noise = noise_prob + (eve_prob * 0.25)

    alice_bits = np.random.randint(2, size=n_qubits).astype(int)
    alice_bases = np.random.randint(2, size=n_qubits).astype(int)
    bob_bases = np.random.randint(2, size=n_qubits).astype(int)
    
    # --- SIMULATION CORE (REPLACING QISKIT) ---
    measured_bits = []
    for i in range(n_qubits):
        # 1. Determine the IDEAL measured bit (no noise)
        ideal_bit = -1
        if alice_bases[i] == bob_bases[i]:
            # Bases match: Bob measures Alice's bit
            ideal_bit = alice_bits[i]
        else:
            # Bases mismatch: Bob measures a random bit (50/50 chance)
            ideal_bit = np.random.randint(2)
            
        # 2. Apply Readout Noise / Eavesdropping Effect (Bit-Flip)
        final_bit = ideal_bit
        if np.random.rand() < effective_readout_noise:
            # Flip the bit (0 -> 1, 1 -> 0)
            final_bit = 1 - ideal_bit
        
        measured_bits.append(final_bit)
    
    # --- KEY SIFTING & QBER CALCULATION ---

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
    
    # QBER estimation
    est_size = max(1, sifted_length // 2)
    est_indices = np.random.choice(range(sifted_length), est_size, replace=False)
    errors = sum(alice_sifted[j] != bob_sifted[j] for j in est_indices)
    qber = errors / est_size

    # Eavesdropping detection
    total_errors = sum(alice_sifted[j] != bob_sifted[j] for j in range(sifted_length))
    detected_eve = (qber > QBER_THRESHOLD) or (total_errors > 0)

    # Final Key generation
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