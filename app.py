from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import config
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# Initialize encryption
key = Fernet.generate_key()
cipher_suite = Fernet(key)

# Simulated database
patients_db = {}

# Admin credentials
admins = {
    "admin": generate_password_hash("securepassword123")
}

@app.route('/')
def home():
    return redirect(url_for('common_portal'))

@app.route('/common')
def common_portal():
    safe_patient_data = []
    for pid, patient in patients_db.items():
        safe_patient_data.append({
            "id": pid,
            "name": patient["name"],
            "age": patient["age"],
            "created_at": patient.get("created_at", "N/A"),
            "has_encrypted": True if patient.get("encrypted") else False
        })
    return render_template('common.html', patients=safe_patient_data)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in admins and check_password_hash(admins[username], password):
            session['admin'] = username
            return redirect(url_for('admin_portal'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/portal')
def admin_portal():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    decrypted_patient_data = []
    for pid, patient in patients_db.items():
        try:
            decrypted = cipher_suite.decrypt(patient['encrypted'].encode()).decode()
            diagnosis, medication = decrypted.split('|||')
            
            decrypted_patient_data.append({
                "id": pid,
                "name": patient["name"],
                "age": patient["age"],
                "diagnosis": diagnosis.split(';') if ';' in diagnosis else [diagnosis],
                "medication": medication.split(';') if ';' in medication else [medication],
                "created_at": patient.get("created_at", "N/A")
            })
        except Exception as e:
            print(f"Error decrypting patient {pid}: {str(e)}")
            continue
    
    return render_template('admin_portal.html', patients=decrypted_patient_data)

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            # Generate unique patient ID
            patient_id = 'patient_' + str(uuid.uuid4())[:8]
            
            # Get form data
            name = request.form.get('name').strip()
            age = request.form.get('age').strip()
            diagnoses = [d.strip() for d in request.form.getlist('diagnoses[]') if d.strip()]
            medications = [m.strip() for m in request.form.getlist('medications[]') if m.strip()]
            
            # Validate input
            if not name or not age or not diagnoses or not medications:
                flash('All fields are required', 'danger')
                return redirect(url_for('add_patient'))
            
            # Create patient record
            patient_data = {
                "name": name,
                "age": int(age),
                "encrypted": None,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Prepare sensitive data (join multiple values with semicolon)
            sensitive_data = f"{';'.join(diagnoses)}|||{';'.join(medications)}"
            patient_data['encrypted'] = cipher_suite.encrypt(sensitive_data.encode()).decode()
            
            # Add to database
            patients_db[patient_id] = patient_data
            flash('Patient added successfully!', 'success')
            return redirect(url_for('admin_portal'))
        
        except ValueError:
            flash('Age must be a number', 'danger')
        except Exception as e:
            flash(f'Error adding patient: {str(e)}', 'danger')
    
    return render_template('add_patient.html')

@app.route('/delete_patient/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if patient_id in patients_db:
        del patients_db[patient_id]
        flash('Patient deleted successfully!', 'success')
    else:
        flash('Patient not found!', 'danger')
    
    return redirect(url_for('admin_portal'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('common_portal'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)