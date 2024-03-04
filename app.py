from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin  
from flask_admin.contrib.sqla import ModelView
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your_secret_key' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///serial_keys.db' 
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class SerialKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    added_date = db.Column(db.DateTime, default=datetime.utcnow)
db.create_all()

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return render_template('index.html') 

@app.route('/admin')
def admin_dashboard():
    if 'username' in session:
        serial_keys = SerialKey.query.all()
        return render_template('admin.html', serial_keys=serial_keys)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', message='Invalid username or password')
    return render_template('login.html', message='')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin/addSerialKey', methods=['POST'])
def add_serial_key():
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    key = request.form.get('key')
    if key is None:
        return jsonify({'error': 'Key not found in request'}), 400

    existing_key = SerialKey.query.filter_by(key=key).first()
    if existing_key:
        serial_keys = SerialKey.query.all()
        return render_template('admin.html', serial_keys=serial_keys, error_message='Key already exists')
    
    new_key = SerialKey(key=key)
    db.session.add(new_key)
    db.session.commit()
    
    serial_keys = SerialKey.query.all()
    
    return render_template('admin.html', serial_keys=serial_keys, success_message='Serial key added successfully')
@app.route('/verifySerialKey', methods=['POST'])
def verify_serial_key():
    key = request.form.get('key')
    if key is None:
        return render_template('error.html', message='Key not found in request'), 400

    serial_key = SerialKey.query.filter_by(key=key).first()
    if serial_key:
        verification_result = True
    else:
        verification_result = False

    return render_template('verification_result.html', verified=verification_result)



@app.route('/admin/deleteSerialKey/<int:key_id>', methods=['GET', 'POST'])
def delete_serial_key(key_id):
    if 'username' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    key = SerialKey.query.get(key_id)
    if key:
        db.session.delete(key)
        db.session.commit()
        return redirect(url_for('admin_dashboard', success_message='Serial key deleted successfully'))
    else:
        return redirect(url_for('admin_dashboard', error_message='Serial key not found')), 404



def delete_all_data():
    try:
        db.session.query().delete()
        db.session.commit()
        print("All data deleted successfully.")
    except Exception as e:
        db.session.rollback()
        print("An error occurred while deleting data:", str(e))

@app.route('/delete_all_data')
def trigger_delete_all_data():
    delete_all_data()
    return 'All data has been deleted.'    

if __name__ == '__main__':
    app.run(debug=True)
