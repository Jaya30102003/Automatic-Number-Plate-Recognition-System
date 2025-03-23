# Automatic Number Plate Recognition System
## 📌 Overview
This is a web-based Automatic Number Plate Recognition (ANPR) system built using Flask for the backend and HTML, CSS, and minimal JavaScript for the frontend. It detects license plate numbers from uploaded images and retrieves vehicle owner details from a database. The system also manages fines associated with detected vehicles.

## 🚀 Features
- License Plate Detection using YOLOv5
- Text Extraction using EasyOCR
- SQLite3 Database for storing vehicle and fine details
- Admin Authentication for secure access
- Vehicle Management (Add, Update, Delete vehicle details)
- Fine Management (Add, View, Delete fines)

## 🛠️ Tech Stack
- Backend: Flask, SQLAlchemy, SQLite3
- Frontend: HTML, CSS, JavaScript
- Machine Learning: YOLOv5, EasyOCR
- Libraries Used: OpenCV, NumPy, Pillow

## 🔍 How It Works
- Upload an image of a vehicle license plate.
- The system detects the plate using YOLOv5 and extracts text using EasyOCR.
- The detected number is matched against the database.
- If a match is found, vehicle details are displayed.
- Users can manage fines and update records.
