import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
# NOTE: We remove imports from qiskit_aer (AerSimulator, NoiseModel, etc.)

QBER_THRESHOLD = 0.11

def bb84_protocol(n_qubits=10, noise_prob=0.0, eve_prob=0.0):
    """
    Full BB84 protocol simulation, simulating noise and readout errors with NumPy.
    """
    effective_readout_noise = noise_prob + (eve_prob * 0.25)

    alice_bits = np.random.randint(2, size=n_qubits).astype(int)
    alice_bases = np.random.randint(2, size=n_qubits).astype(int)
    bob_bases = np.random.randint(2, size=n_qubits).astype(int)
    
    # --- Alice encodes ---
    # The actual quantum simulation is simplified to determining the correct bit
    # assuming an ideal run, and then applying noise later.
    ideal_measured_bits = []
    
    for i in range(n_qubits):
        # The bit Bob measures ideally depends on:
        # 1. Alice's initial bit (alice_bits[i])
        # 2. Whether their bases match (alice_bases[i] == bob_bases[i])
        
        if alice_bases[i] == bob_bases[i]:
            # Bases match: Bob measures Alice's bit (ideal_measured_bit = alice_bits[i])
            ideal_measured_bits.append(alice_bits[i])
        else:
            # Bases mismatch: Bob measures a random bit (50/50 chance)
            ideal_measured_bits.append(np.random.randint(2))
    
    # --- Simulate Readout Noise and Eavesdropping Effects (post-measurement) ---
    measured_bits = []
    for i in range(n_qubits):
        ideal_bit = ideal_measured_bits[i]
        
        # effective_readout_noise is the probability of flipping the bit
        if np.random.rand() < effective_readout_noise:
            # Flip the bit due to error
            measured_bits.append(1 - ideal_bit)
        else:
            # Keep the ideal bit
            measured_bits.append(ideal_bit)

    # Note: Gate noise (effective_gate_noise) is implicitly covered by 
    # the overall effective_readout_noise in this simplified, deployment-friendly model.
    
    sifted_indices = [i for i in range(n_qubits) if alice_bases[i] == bob_bases[i]]
    alice_sifted = [int(alice_bits[i]) for i in sifted_indices]
    bob_sifted = [measured_bits[i] for i in sifted_indices]
    sifted_length = len(sifted_indices)

    # The rest of the protocol logic remains the same (sifting, QBER calculation, etc.)
    # ... [Keep the rest of the original function exactly as it was from here] ...
    # (The QBER, final key, and return dictionary logic)
    
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