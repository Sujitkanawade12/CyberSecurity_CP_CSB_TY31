document.addEventListener('DOMContentLoaded', function() {
    // Add field functionality for diagnoses and medications
    function addField(type) {
        const container = document.getElementById(`${type}-container`);
        const newField = document.createElement('div');
        newField.className = 'input-group mb-2';
        newField.innerHTML = `
            <input type="text" class="form-control" name="${type}[]" placeholder="Enter ${type.slice(0, -1)}" required>
            <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">
                <i class="bi bi-trash"></i> Remove
            </button>
        `;
        container.appendChild(newField);
    }

    // Expose to global scope for button clicks
    window.addField = addField;

    // Form validation for add patient
    const patientForm = document.getElementById('patientForm');
    if (patientForm) {
        patientForm.addEventListener('submit', function(e) {
            const diagnoses = document.getElementsByName('diagnoses[]');
            const medications = document.getElementsByName('medications[]');
            
            let valid = true;
            
            // Check at least one diagnosis and medication
            if (diagnoses.length === 0 || medications.length === 0) {
                valid = false;
                alert('Please add at least one diagnosis and one medication');
            }
            
            // Check all fields have values
            const inputs = patientForm.querySelectorAll('input[required]');
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('is-invalid');
                } else {
                    input.classList.remove('is-invalid');
                }
            });
            
            if (!valid) {
                e.preventDefault();
            }
        });
    }

    // Auto-focus first input in forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const firstInput = form.querySelector('input');
        if (firstInput) {
            firstInput.focus();
        }
    });
});