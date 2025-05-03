document.addEventListener('DOMContentLoaded', function() {
    const toggleAllBtn = document.getElementById('toggleAllBtn');
    let allDecrypted = false;

    function updateRowWithData(row, data) {
        const fields = ['age', 'gender', 'blood_group', 'diagnosis', 
                       'prescribed_meds', 'generic_alternatives', 
                       'dosages', 'allergies', 'notes'];
        
        fields.forEach((field, idx) => {
            const cell = row.querySelector(`td:nth-child(${idx + 3})`);
            if (cell) {
                cell.textContent = data[field] || 'None';
                cell.classList.replace('private-field', 'decrypted-field');
            }
        });
    }

    function resetRowToEncrypted(row) {
        row.querySelectorAll('.decrypted-field').forEach((cell, idx) => {
            cell.textContent = '🔒 Encrypted';
            cell.classList.replace('decrypted-field', 'private-field');
        });
    }

    // Toggle single patient encryption
    document.querySelectorAll('.toggle-encryption-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const patientId = this.dataset.patientId;
            const row = document.querySelector(`tr[data-patient-id="${patientId}"]`);
            
            this.innerHTML = '<span class="loading-indicator"></span> Processing...';
            this.disabled = true;
            
            try {
                const response = await fetch(`/toggle_encryption/${patientId}`);
                const data = await response.json();
                
                if (data.error) throw new Error(data.error);
                
                if (data.status === 'decrypted') {
                    updateRowWithData(row, data.data);
                    this.innerHTML = '<i class="bi bi-lock"></i> Encrypt';
                    if (!allDecrypted) {
                        toggleAllBtn.innerHTML = '<i class="bi bi-lock"></i> Encrypt All';
                    }
                } else {
                    resetRowToEncrypted(row);
                    this.innerHTML = '<i class="bi bi-unlock"></i> Decrypt';
                    if (allDecrypted) {
                        toggleAllBtn.innerHTML = '<i class="bi bi-unlock"></i> Decrypt All';
                    }
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Operation failed: ' + error.message);
                this.innerHTML = '<i class="bi bi-unlock"></i> Decrypt';
            } finally {
                this.disabled = false;
            }
        });
    });

    // Toggle all encryption
    toggleAllBtn.addEventListener('click', async function() {
        const action = allDecrypted ? "encrypt" : "decrypt";
        this.innerHTML = '<span class="loading-indicator"></span> Processing...';
        this.disabled = true;
        
        try {
            const response = await fetch('/toggle_all_encryption', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ action })
            });
            
            const data = await response.json();
            
            data.results.forEach(result => {
                const row = document.querySelector(`tr[data-patient-id="${result.patient_id}"]`);
                if (!row) return;
                
                const btn = row.querySelector('.toggle-encryption-btn');
                
                if (result.status === 'decrypted') {
                    updateRowWithData(row, result.data);
                    if (btn) btn.innerHTML = '<i class="bi bi-lock"></i> Encrypt';
                } else {
                    resetRowToEncrypted(row);
                    if (btn) btn.innerHTML = '<i class="bi bi-unlock"></i> Decrypt';
                }
            });
            
            allDecrypted = !allDecrypted;
            this.innerHTML = allDecrypted 
                ? '<i class="bi bi-lock"></i> Encrypt All' 
                : '<i class="bi bi-unlock"></i> Decrypt All';
        } catch (error) {
            console.error('Error:', error);
            alert('Operation failed: ' + error.message);
            this.innerHTML = allDecrypted 
                ? '<i class="bi bi-lock"></i> Encrypt All' 
                : '<i class="bi bi-unlock"></i> Decrypt All';
        } finally {
            this.disabled = false;
        }
    });
});