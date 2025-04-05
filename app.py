from flask import Flask, render_template, url_for, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

from flask_sqlalchemy import SQLAlchemy
import sqlite3
import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = '12345'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///details.db'  

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_BINDS'] = {
    'details_db': f"sqlite:///{os.path.join(BASE_DIR, 'details.db')}",
    'fines_db': f"sqlite:///{os.path.join(BASE_DIR, 'fines.db')}",
    'users_db': f"sqlite:///{os.path.join(BASE_DIR, 'users.db')}"
}


db = SQLAlchemy(app)

class Details(db.Model):
    __bind_key__ = 'details_db'
    id = db.Column(db.Integer, primary_key=True)
    veh_no = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    owner = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Details {self.veh_no}>'

class Fines(db.Model):
    __bind_key__ = 'fines_db'
    id = db.Column(db.Integer, primary_key=True)
    veh_no = db.Column(db.String(20), nullable=False)
    violation = db.Column(db.String(100), nullable=False)
    fine_amount = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Fine {self.veh_no} - {self.violation}>"

class User(db.Model):
    __bind_key__ = 'users_db'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


UPLOAD_FOLDER = 'static/' 
model = YOLO(r'C:\Users\Dell\OneDrive\Desktop\ANPR\best.pt')  # Replace with your YOLO model path
reader = easyocr.Reader(['en'], gpu=False)  # EasyOCR initialized

def extract_text_easyocr(image_input):
    if isinstance(image_input, np.ndarray):
        image = image_input
    else:
        raise ValueError("Invalid input type. Provide a NumPy array.")
    
    results = reader.readtext(image)
    extracted_text = " ".join([text for (_, text, _) in results])
    return extracted_text


@app.route('/')
def home1():
    return render_template('index1.html')

@app.route('/admin', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        if user == 'admin' and password == '****':
            session['user'] = user
            return redirect(url_for('details'))
        else:
            message = 'Try again. The credentials are not correct'
            return render_template('home.html', message=message)

    return render_template('home.html')

@app.route('/details', methods=['POST', 'GET'])
def details():
    if 'user' not in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        veh_no = request.form['vehno']
        veh_owner = request.form['owner']
        veh_address = request.form['address']

        new_data = Details(veh_no=veh_no, address=veh_address, owner=veh_owner)

        try:
            db.session.add(new_data)
            db.session.commit()
            return redirect('/details')
        except:
            return 'Issue faced'

    details = Details.query.order_by(Details.id).all()
    return render_template('index.html', details=details)

@app.route('/details/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect(url_for('home'))

    data_to_delete = Details.query.get_or_404(id)

    try:
        db.session.delete(data_to_delete)
        db.session.commit()
        return redirect('/details')
    except:
        return 'Issue encountered in deleting'

@app.route('/details/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'user' not in session:
        return redirect(url_for('home'))

    detail = Details.query.get_or_404(id)
    if request.method == 'POST':
        detail.veh_no = request.form['vehno']
        detail.owner = request.form['owner']
        detail.address = request.form['address']
        try:
            db.session.commit()
            return redirect('/details')
        except:
            return 'Issue faced at update task'
    return render_template('update.html', detail=detail)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))  

@app.route('/fines', methods=['GET', 'POST'])
def fines_page():
    conn = sqlite3.connect('fines.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        veh_no = request.form['veh_no']
        violation = request.form['violation']
        fine_amount = request.form['fine_amount']

        cursor.execute("INSERT INTO fines (veh_no, violation, fine_amount) VALUES (?, ?, ?)",
                       (veh_no, violation, fine_amount))
        conn.commit()

    cursor.execute("SELECT * FROM fines")
    fines = cursor.fetchall()
    
    conn.close()
    return render_template('add_fine.html', fines=fines)


@app.route('/delete_fine/<int:fine_id>', methods=['POST'])
def delete_fine(fine_id):
    conn = sqlite3.connect('fines.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM fines WHERE id = ?", (fine_id,))
    conn.commit()
    
    conn.close()
    return redirect(url_for('fines_page'))

@app.route('/vehicle_fines/<veh_no>')
def vehicle_fines(veh_no):
    conn = sqlite3.connect('details.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM details WHERE veh_no = ?", (veh_no,))
    vehicle_detail = cursor.fetchone()

    conn.close()
    
    conn = sqlite3.connect('fines.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM fines WHERE veh_no = ?", (veh_no,))
    fines = cursor.fetchall()

    total_fine = sum(fine[3] for fine in fines) if fines else 0

    conn.close()

    return render_template('fines.html', detail=vehicle_detail, fines=fines, total_fine=total_fine)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('user_login'))
        except:
            flash('Username already exists. Try another.', 'danger')
    return render_template('register.html')

@app.route('/user', methods=['GET', 'POST'])
def user_login():
    message = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user'] = username
            return redirect(url_for('user_home'))
        else:
            message = 'Invalid credentials. Try again.'
    return render_template('user_login.html',message = message)

@app.route('/user_home')
def user_home():
    if request.method == 'POST':
        if 'image' not in request.files:
            message = "No image file uploaded."
            return render_template('retrieve.html', message=message)
        
        image = request.files['image']
        if image.filename == '':
            message = "No selected image."
            return render_template('retrieve.html', message=message)

        image_filename = os.path.join(UPLOAD_FOLDER, image.filename)
        image.save(image_filename)

        try:
            img = Image.open(image.stream)
            img = np.array(img)

            results = model(img)

            if len(results[0].boxes) == 0:
                message = "No license plate detected."
                return render_template('retrieve.html', image_path=image_filename, detected_text=None, detail=None, message=message)

            box = results[0].boxes[0]  
            x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())

            license_plate_img = img[y_min:y_max, x_min:x_max]

            license_plate_img_rgb = cv2.cvtColor(license_plate_img, cv2.COLOR_BGR2RGB)

            license_plate_text = extract_text_easyocr(license_plate_img_rgb).strip().upper()

            if not license_plate_text:
                message = "Could not detect license plate text."
                return render_template('retrieve.html', image_path=image_filename, detected_text=None, detail=None, message=message)

            detail = Details.query.filter_by(veh_no=license_plate_text).first()

            if detail:
                return render_template('retrieve.html', image_path=image_filename, detected_text=license_plate_text, detail=detail, message=None)
            else:
                message = f"Vehicle number '{license_plate_text}' not found in the database."
                return render_template('retrieve.html', image_path=image_filename, detected_text=license_plate_text, detail=None, message=message)

        except Exception as e:
            message = f"Error processing the image: {str(e)}"
            return render_template('retrieve.html', message=message)

    return render_template('retrieve.html')

import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2

@app.route('/upload', methods=['POST'])
def upload():
    image_data = request.form['image']
    # Decode the base64 image data
    image_data = image_data.split(',')[1]
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    # Convert PIL image to OpenCV format
    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Process the image with your model and EasyOCR
    results = model(image_cv)

    if len(results[0].boxes) == 0:
        message = "No license plate detected."
        return render_template('retrieve.html', message=message)

    box = results[0].boxes[0]
    x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())
    license_plate_img = image_cv[y_min:y_max, x_min:x_max]
    license_plate_img_rgb = cv2.cvtColor(license_plate_img, cv2.COLOR_BGR2RGB)
    license_plate_text = extract_text_easyocr(license_plate_img_rgb).strip().upper()

    if not license_plate_text:
        message = "Could not detect license plate text."
        return render_template('retrieve.html', message=message)

    detail = Details.query.filter_by(veh_no=license_plate_text).first()

    if detail:
        return render_template('retrieve.html', detected_text=license_plate_text, detail=detail)
    else:
        message = f"Vehicle number '{license_plate_text}' not found in the database."
        return render_template('retrieve.html', message=message)


@app.route('/user_logout')
def user_logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('user_login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  
        engine_details = db.engines['details_db']
        Details.metadata.create_all(engine_details)

        engine_fines = db.engines['fines_db']
        Fines.metadata.create_all(engine_fines)

        engine_users = db.engines['users_db']
        User.metadata.create_all(engine_users)

    app.run(debug=True)