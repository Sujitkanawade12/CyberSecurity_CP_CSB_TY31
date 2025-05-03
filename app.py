from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import config
import uuid
from datetime import datetime
import base64
import csv
import os
import json

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# CSV file configuration
CSV_FILE = 'patient_data.csv'
CSV_FIELDS = ['patient_id', 'name', 'created_at', 'encrypted_data']

# Generate RSA keys
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)
public_key = private_key.public_key()

# Simulated database
patients_db = {}

# Admin credentials
admins = {
    "admin": generate_password_hash("securepassword123")
}

# Field configuration
PUBLIC_FIELDS = ["patient_id", "name", "created_at"]
PRIVATE_FIELDS = ["age", "gender", "blood_group", "diagnosis", 
                 "prescribed_meds", "generic_alternatives", 
                 "dosages", "allergies", "notes"]

def load_patients_from_csv():
    if not os.path.exists(CSV_FILE):
        return
        
    with open(CSV_FILE, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            patients_db[row['patient_id']] = {
                'patient_id': row['patient_id'],
                'name': row['name'],
                'created_at': row['created_at'],
                'encrypted': row['encrypted_data']
            }

def save_patients_to_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for patient_id, patient in patients_db.items():
            writer.writerow({
                'patient_id': patient_id,
                'name': patient['name'],
                'created_at': patient['created_at'],
                'encrypted_data': patient.get('encrypted', '')
            })

def encrypt_data(data):
    try:
        # Convert data to JSON string and encode
        data_str = json.dumps(data)
        data_bytes = data_str.encode('utf-8')
        
        # Encrypt the data
        encrypted = public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')
    except Exception as e:
        print(f"Encryption error: {str(e)}")
        raise Exception("Failed to encrypt data")

def decrypt_data(encrypted_data):
    try:
        # Decode from base64
        decoded = base64.b64decode(encrypted_data)
        
        # Decrypt the data
        decrypted = private_key.decrypt(
            decoded,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        # Convert back to dictionary
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"Decryption error: {str(e)}")
        raise Exception("Failed to decrypt data")

# Load existing data on startup
load_patients_from_csv()

@app.route('/')
def home():
    return redirect(url_for('common'))

@app.route('/common')
def common():
    safe_patient_data = []
    for pid, patient in patients_db.items():
        patient_data = {field: patient.get(field) for field in PUBLIC_FIELDS}
        patient_data["has_private"] = bool(patient.get("encrypted"))
        safe_patient_data.append(patient_data)
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
    
    patient_data = []
    for pid, patient in patients_db.items():
        data = {field: patient.get(field) for field in PUBLIC_FIELDS}
        data["encrypted"] = bool(patient.get("encrypted"))
        patient_data.append(data)
    
    return render_template('admin_portal.html', patients=patient_data)

@app.route('/toggle_encryption/<patient_id>')
def toggle_encryption(patient_id):
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    if patient_id not in patients_db:
        return jsonify({"error": "Patient not found"}), 404
    
    patient = patients_db[patient_id]
    
    try:
        if patient.get("decrypted_data"):
            # Re-encrypt the data
            encrypted_data = encrypt_data(patient["decrypted_data"])
            patient["encrypted"] = encrypted_data
            del patient["decrypted_data"]
            save_patients_to_csv()
            return jsonify({"status": "encrypted"})
        else:
            # Decrypt the data
            if not patient.get('encrypted'):
                return jsonify({"error": "No encrypted data found"}), 400
                
            decrypted_data = decrypt_data(patient['encrypted'])
            patient["decrypted_data"] = decrypted_data
            save_patients_to_csv()
            return jsonify({
                "status": "decrypted",
                "data": {**{f: patient.get(f) for f in PUBLIC_FIELDS}, **decrypted_data}
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/toggle_all_encryption', methods=['POST'])
def toggle_all_encryption():
    if 'admin' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    action = request.json.get('action')
    results = []
    
    for pid in patients_db:
        patient = patients_db[pid]
        try:
            if action == "decrypt":
                if not patient.get("decrypted_data"):
                    decrypted_data = decrypt_data(patient['encrypted'])
                    patient["decrypted_data"] = decrypted_data
                    results.append({
                        "patient_id": pid,
                        "status": "decrypted",
                        "data": {**{f: patient.get(f) for f in PUBLIC_FIELDS}, **decrypted_data}
                    })
            elif action == "encrypt":
                if patient.get("decrypted_data"):
                    encrypted_data = encrypt_data(patient["decrypted_data"])
                    patient["encrypted"] = encrypted_data
                    del patient["decrypted_data"]
                    results.append({
                        "patient_id": pid,
                        "status": "encrypted"
                    })
        except Exception as e:
            results.append({
                "patient_id": pid,
                "error": str(e)
            })
    
    save_patients_to_csv()
    return jsonify({"results": results})

@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        try:
            patient_id = f"PT-{uuid.uuid4().hex[:6].upper()}"
            
            public_data = {
                "patient_id": patient_id,
                "name": request.form.get('name', '').strip(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if not public_data['name']:
                flash('Patient name is required', 'danger')
                return redirect(url_for('add_patient'))
            
            private_data = {
                "age": request.form.get('age', ''),
                "gender": request.form.get('gender', ''),
                "blood_group": request.form.get('blood_group', ''),
                "diagnosis": request.form.get('diagnosis', ''),
                "prescribed_meds": request.form.get('prescribed_meds', ''),
                "generic_alternatives": request.form.get('generic_alternatives', ''),
                "dosages": request.form.get('dosages', ''),
                "allergies": request.form.get('allergies', ''),
                "notes": request.form.get('notes', '')
            }
            
            encrypted_data = encrypt_data(private_data)
            patients_db[patient_id] = {**public_data, "encrypted": encrypted_data}
            save_patients_to_csv()
            
            flash('Patient added successfully!', 'success')
            return redirect(url_for('admin_portal'))
        
        except Exception as e:
            flash(f'Error adding patient: {str(e)}', 'danger')
    
    return render_template('add_patient.html',
                         blood_groups=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])

@app.route('/delete_patient/<patient_id>', methods=['POST'])
def delete_patient(patient_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    
    if patient_id in patients_db:
        del patients_db[patient_id]
        save_patients_to_csv()
        flash('Patient deleted successfully!', 'success')
    else:
        flash('Patient not found!', 'danger')
    
    return redirect(url_for('admin_portal'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('common'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)

