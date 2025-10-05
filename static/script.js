// Global variables to store chart instances
let noiseChartInstance = null;
let eveChartInstance = null;

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // NOTE: 'event' is not defined unless passed in or accessed via window.event.
    // For robust use, you should ensure the function receives the event object, 
    // or use a closure/anonymous function to access it. Assuming it's called 
    // directly from an event listener where 'event' is available.
    if (typeof event !== 'undefined' && event.target) {
        event.target.classList.add('active');
    } else {
        // Fallback for direct calls if 'event' isn't available
        const btn = document.querySelector(`.tab-btn[onclick="switchTab('${tabName}')"]`);
        if (btn) btn.classList.add('active');
    }

    document.getElementById(`${tabName}-tab`).classList.add('active');
}

document.getElementById('sim-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        n_qubits: parseInt(document.getElementById('n_qubits').value),
        noise_prob: parseFloat(document.getElementById('noise_prob').value),
        eve_prob: parseFloat(document.getElementById('eve_prob').value)
    };
    
    document.getElementById('loading').style.display = 'flex';
    
    try {
        const response = await fetch('/simulate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        document.getElementById('qber').textContent = data.qber.toFixed(4);
        document.getElementById('sifted_length').textContent = data.sifted_length;
        document.getElementById('key_length').textContent = data.key_length;
        document.getElementById('detected_eve').textContent = data.detected_eve ? 'Yes' : 'No';
        document.getElementById('detected_eve').style.color = data.detected_eve ? 'red' : 'green';
        
        // Ensure keys are displayed cleanly (handle empty arrays gracefully)
        document.getElementById('alice_key').textContent = data.alice_final_key.slice(0, 20).join('') || 'Key not established';
        document.getElementById('bob_key').textContent = data.bob_final_key.slice(0, 20).join('') || 'Key not established';
        
        document.getElementById('results').style.display = 'block';
    } catch (error) {
        alert('Error running simulation: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

document.getElementById('analysis-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        n_runs: parseInt(document.getElementById('n_runs').value),
        n_qubits: parseInt(document.getElementById('n_qubits_analysis').value)
    };
    
    document.getElementById('loading').style.display = 'flex';
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        // --- NOISE CHART FIX ---
        const noiseCtx = document.getElementById('noiseChart').getContext('2d');
        // Check if an instance already exists and destroy it
        if (noiseChartInstance) {
            noiseChartInstance.destroy();
        }

        // Create the new Noise Chart instance and store it
        noiseChartInstance = new Chart(noiseCtx, {
            type: 'line',
            data: {
                labels: data.noise.x,
                datasets: [{
                    label: 'QBER vs Natural Noise',
                    data: data.noise.qber,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Effect of Natural Channel Noise on QBER'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Noise Probability (%)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'QBER'
                        }
                    }
                }
            }
        });
        
        // --- EVE CHART FIX ---
        const eveCtx = document.getElementById('eveChart').getContext('2d');
        // Check if an instance already exists and destroy it
        if (eveChartInstance) {
            eveChartInstance.destroy();
        }

        // Create the new Eve Chart instance and store it
        eveChartInstance = new Chart(eveCtx, {
            type: 'line',
            data: {
                labels: data.eve.x,
                datasets: [{
                    label: 'QBER',
                    data: data.eve.qber,
                    borderColor: 'rgb(255, 99, 132)',
                    yAxisID: 'y',
                    tension: 0.1
                }, {
                    label: 'Detection Rate',
                    data: data.eve.detection_rate,
                    borderColor: 'rgb(54, 162, 235)',
                    yAxisID: 'y1',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Effect of Eavesdropping on QBER and Detection Rate'
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Eavesdropper Probability (%)'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'QBER'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Detection Rate'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
        
        document.getElementById('charts').style.display = 'block';
    } catch (error) {
        // The alert here will now display any network or server-side error, 
        // as the client-side chart error is handled.
        alert('Error running analysis: ' + error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});