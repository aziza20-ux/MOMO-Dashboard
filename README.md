# MoMo SMS Dashboard

This project is a web application built with Flask and SQLAlchemy to manage and visualize your Mobile Money (MoMo) SMS transaction data. Users can upload their SMS backup XML files, and the application will parse the data, store it in a database, and display it on a dashboard.

### Features
- User Registration and Authentication

- XML SMS Data Upload

- Parsing and Storage of SMS Data in a SQLite database

- Dashboard to view aggregated and detailed SMS transactions

### Project Structure

MoMoSMSDashboard/
├── backend/
│   ├── app.py           # Main server entry
│   ├── auth.py          # Authentication logic
│   ├── parser.py        # SMS parsing logic
│   ├── cleaner.py       # Data cleaning logic (placeholder)
│   ├── dashboard.py     # Chart & data display logic
│   ├── middleware.py    # Route protection
│   ├── database.py      # DB connection setup
│   ├── models/
│   │   ├── users.py     # User schema
│   │   └── transactions.py  # Transaction schema
│   └── templates/
│       ├── login.html
│       ├── register.html
│       └── dashboard.html
│       └── 404.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│      └── script.js
│
├── README.md            # Project documentation
├── report.pdf           # Project report (placeholder)

### Setup Instructions

Clone the repository:
""" 
git clone <repository-url>
cd MoMoSMSDashboard
""" 

Create a virtual environment (recommended):

python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

Install dependencies:

pip install Flask SQLAlchemy Werkzeug

(Note: Werkzeug is usually installed with Flask, but explicitly listing it helps if issues arise with password hashing.)

Run the application:

export FLASK_APP=backend/app.py
export FLASK_ENV=development # For development mode with hot-reloading
flask run

The application will typically run on http://127.0.0.1:5000/.

Usage
Register: Navigate to /register to create a new user account.

Login: Use your credentials to log in at /login.

Upload XML: On the dashboard, you will find an option to upload your SMS backup XML file. The application will process this file and populate the database.

View Dashboard: Once data is uploaded, the dashboard will display your SMS transactions.

Database
The application uses SQLite, and the database file sms_database.db will be created in the root directory upon the first run. SQLAlchemy handles the schema definition and migrations automatically.

Contributing
Feel free to contribute to this project.