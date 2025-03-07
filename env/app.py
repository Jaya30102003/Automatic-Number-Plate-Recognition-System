from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///details.db'

db = SQLAlchemy(app)

class Details(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    veh_no = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    owner = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

@app.route('/', methods=['POST', 'GET'])
def home():
    """Show login page first."""
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']

        if user == 'admin' and password == '****':
            session['user'] = user  # Store login session
            return redirect(url_for('details'))  # Redirect to details page after login
        else:
            message = 'Try again. The credentials are not correct'
            return render_template('home.html', message=message)

    return render_template('home.html')  # Show login page first

@app.route('/details', methods=['POST', 'GET'])
def details():
    """Show vehicle details, only if logged in."""
    if 'user' not in session:
        return redirect(url_for('home'))  # If not logged in, redirect to login page

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
    """Delete a record, only if logged in."""
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
    """Update a record, only if logged in."""
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
    """Logout and redirect to login page."""
    session.pop('user', None)
    return redirect(url_for('home'))  

from flask import request, render_template
import cv2
from ultralytics import YOLO
import easyocr
import numpy as np
from PIL import Image
import os

UPLOAD_FOLDER = 'static/' 

# Initialize the model and OCR
model = YOLO(r'C:\Users\Dell\OneDrive\Desktop\ANPR\env\best.pt')  # Replace with your YOLO model path
reader = easyocr.Reader(['en'], gpu=False)  # EasyOCR initialized

def extract_text_easyocr(image_input):
    """Extract text from image using EasyOCR."""
    # Check if input is a NumPy array (image data)
    if isinstance(image_input, np.ndarray):
        image = image_input  # Use directly if it's already an image
    else:
        raise ValueError("Invalid input type. Provide a NumPy array.")
    
    # Run OCR
    results = reader.readtext(image)
    extracted_text = " ".join([text for (_, text, _) in results])
    return extracted_text

@app.route('/retrieve', methods=['GET', 'POST'])
def retrieve():
    """Retrieve vehicle details based on the license plate number extracted from the image."""
    if request.method == 'POST':
        if 'image' not in request.files:
            message = "No image file uploaded."
            return render_template('retrieve.html', message=message)
        
        if 'image' in request.files:
            image = request.files['image']
            image_filename = os.path.join(UPLOAD_FOLDER, image.filename)
            image.save(image_filename)

        file = request.files['image']
        if file.filename == '':
            message = "No selected image."
            return render_template('retrieve.html', message=message)

        if file:
            try:
                # Convert the uploaded image to a NumPy array for processing
                img = Image.open(file.stream)
                img = np.array(img)

                # Run the YOLO model on the image
                results = model(img)

                # If no license plate detected, show a message
                if len(results[0].boxes) == 0:
                    message = "No license plate detected."
                    return render_template('retrieve.html', image_path=image_filename, detected_text=None, detail=None, message=message)

                # Extract the bounding box of the first detected object (license plate)
                box = results[0].boxes[0]  
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0].tolist())

                # Crop the license plate area from the image
                license_plate_img = img[y_min:y_max, x_min:x_max]

                # Convert the cropped license plate image to RGB for OCR
                license_plate_img_rgb = cv2.cvtColor(license_plate_img, cv2.COLOR_BGR2RGB)

                # Use EasyOCR to extract the license plate text
                license_plate_text = extract_text_easyocr(license_plate_img_rgb).strip().upper()

                # If OCR fails to detect text, show a message
                if not license_plate_text:
                    message = "Could not detect license plate text."
                    return render_template('retrieve.html', image_path=image_filename, detected_text=None, detail=None, message=message)

                # Check if the detected license plate is in the database
                detail = Details.query.filter_by(veh_no=license_plate_text).first()

                # If the vehicle is found in the database, show the details
                if detail:
                    return render_template('retrieve.html', image_path=image_filename, detected_text=license_plate_text, detail=detail, message=None)
                else:
                    message = f"Vehicle number '{license_plate_text}' not found in the database."
                    return render_template('retrieve.html', image_path=image_filename, detected_text=license_plate_text, detail=None, message=message)

            except Exception as e:
                message = f"Error processing the image: {str(e)}"
                return render_template('retrieve.html', message=message)

    return render_template('retrieve.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
  # print(app.url_map)
    app.run(debug=True)
