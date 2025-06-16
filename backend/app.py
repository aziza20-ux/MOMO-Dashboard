from flask import Flask, render_template, request, redirect, url_for, flash, session, g, jsonify, Blueprint
from werkzeug.utils import secure_filename
import os

# Import blueprints and database utilities
from auth import auth_bp
from dashboard import (
    get_user_transactions, get_transaction_summary, 
    get_transaction_volume_by_type, get_monthly_transaction_volume, # Corrected import name
    get_amount_distribution_summary, get_transaction_by_id
)
from database import init_db # Import init_db for database initialization
from middleware import login_required
from parser import parse_sms_xml_content, insert_transactions_from_parsed_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_should_be_changed')
app.config['UPLOAD_FOLDER'] = 'uploads' # Directory to temporarily store uploaded files
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register blueprints
app.register_blueprint(auth_bp)

# Initialize the database when the app starts
with app.app_context():
    init_db()

@app.before_request
def load_logged_in_user():
    """
    Loads the logged-in user's ID into Flask's global 'g' object
    before each request if a user is in the session.
    """
    user_id = session.get('user_id')
    if user_id is None:
        g.user_id = None
        g.username = None
    else:
        g.user_id = user_id
        g.username = session.get('username')

@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return render_template('404.html'), 404

@app.route('/')
def index():
    """Redirects to the dashboard if logged in, otherwise to login."""
    if 'user_id' in session:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Displays the user's SMS dashboard with filtering options and charts.
    """
    user_id = g.user_id
    username = g.username

    # Get filter parameters from query string
    transaction_type = request.args.get('transaction_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)

    # Fetch filtered transactions
    transactions = get_user_transactions(
        user_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=50 # Limiting for display in table
    )
    
    # Fetch summary and chart data (these are not filtered by request.args directly,
    # they summarize ALL data for the user, unless specific filterable charts are needed)
    summary_counts = get_transaction_summary(user_id) # Counts of SMS types
    
    # Data for charts
    chart_volume_by_type = get_transaction_volume_by_type(user_id) # Total amount by type
    chart_monthly_volume = get_monthly_transaction_volume(user_id) # Total amount per month
    chart_amount_distribution = get_amount_distribution_summary(user_id) # Total received vs. sent amounts

    return render_template(
        'dashboard.html',
        username=username,
        transactions=transactions,
        summary_counts=summary_counts,
        chart_volume_by_type=chart_volume_by_type,
        chart_monthly_volume=chart_monthly_volume,
        chart_amount_distribution=chart_amount_distribution,
        # Pass filter values back to the template to pre-fill the form
        current_filters={
            'transaction_type': transaction_type,
            'start_date': start_date,
            'end_date': end_date,
            'min_amount': min_amount,
            'max_amount': max_amount
        }
    )

@app.route('/upload_xml', methods=['POST'])
@login_required
def upload_xml():
    user_id = g.user_id
    if 'xml_file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('dashboard'))  # Use the correct route name

    file = request.files['xml_file']

    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('dashboard'))  # Use the correct route name

    if file and file.filename.endswith('.xml'):
        xml_content = file.read().decode('utf-8')

        parsed_data = parse_sms_xml_content(xml_content)
        if parsed_data:
            inserted_count = insert_transactions_from_parsed_data(user_id, parsed_data)
            flash(f'Successfully uploaded and processed {inserted_count} SMS records.', 'success')
        else:
            flash('Failed to parse XML or no SMS records found.', 'error')
    else:
        flash('Invalid file type. Please upload an XML file.', 'error')

    return redirect(url_for('dashboard'))  # Use the correct route name

@app.route('/api/transaction/<int:transaction_id>')
@login_required
def get_transaction_details_api(transaction_id):
    """
    API endpoint to get detailed information for a single transaction.
    Returns JSON.
    """
    user_id = g.user_id
    transaction = get_transaction_by_id(user_id, transaction_id)

    if transaction:
        # Convert Transaction object to a dictionary for JSON serialization
        transaction_dict = {
            'id': transaction.id,
            'protocol': transaction.protocol,
            'address': transaction.address,
            'date': transaction.date,
            'type': transaction.type,
            'subject': transaction.subject,
            'body': transaction.body,
            'toa': transaction.toa,
            'sc_toa': transaction.sc_toa,
            'service_center': transaction.service_center,
            'read': transaction.read,
            'status': transaction.status,
            'locked': transaction.locked,
            'date_sent': transaction.date_sent,
            'sub_id': transaction.sub_id,
            'readable_date': transaction.readable_date,
            'contact_name': transaction.contact_name,
            'amount': transaction.amount
        }
        return jsonify(transaction_dict)
    else:
        return jsonify({'error': 'Transaction not found or unauthorized'}), 404

# Define a main blueprint for non-auth routes (like dashboard, index)
main_bp = Blueprint('main', __name__)
app.register_blueprint(main_bp) # Register main_bp after its routes are defined if they are here
