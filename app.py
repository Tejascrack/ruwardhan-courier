from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ruwardhan_courier_secure_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courier.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(10), unique=True, nullable=False)
    sender_name = db.Column(db.String(100), nullable=False)
    receiver_name = db.Column(db.String(100), nullable=False)
    receiver_address = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='In Transit')

def generate_tracking_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

with app.app_context():
    db.create_all()

# ----------------- ROUTES -----------------

@app.route('/')
def index():
    return redirect(url_for('admin_login'))

@app.route('/track_home')
def track_home():
    return render_template('index.html')

@app.route('/track', methods=['POST'])
def track():
    track_id = request.form.get('tracking_id', '').strip().upper()
    shipment = Shipment.query.filter_by(tracking_id=track_id).first()
    return render_template('index.html', result=shipment, searched=True, query_id=track_id)

@app.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        tracking_code = generate_tracking_id()
        new_shipment = Shipment(
            tracking_id=tracking_code,
            sender_name=request.form.get('sender_name', '').strip(),
            receiver_name=request.form.get('receiver_name', '').strip(),
            receiver_address=request.form.get('receiver_address', '').strip(),
            status='In Transit'
        )
        db.session.add(new_shipment)
        db.session.commit()
        return render_template('book.html', new_id=tracking_code)
    return render_template('book.html')

@app.route('/receipt/<tracking_id>')
def receipt(tracking_id):
    shipment = Shipment.query.filter_by(tracking_id=tracking_id).first_or_404()
    return render_template('receipt.html', s=shipment)

@app.route('/calculator')
def calculator():
    return render_template('calculator.html')

# ADMIN AUTHENTICATION
ADMIN_USER = "abhijeet"
ADMIN_PASS = "abhijeet9028"

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['admin_logged_in'] = True
            return redirect(url_for('operations'))
        else:
            flash('Invalid admin credentials. Please try again.')
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/operations')
def operations():
    # If not logged in, force redirect to login page
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    try:
        shipments = Shipment.query.order_by(Shipment.id.desc()).all()
    except Exception:
        shipments = []

    total = len(shipments)
    in_transit = sum(1 for s in shipments if s.status == 'In Transit')
    delivered = sum(1 for s in shipments if s.status == 'Delivered')
    pending = sum(1 for s in shipments if s.status in ['Order Booked', 'Pending Pickup', 'Order Received'])

    return render_template(
        'operations.html',
        shipments=shipments,
        total=total,
        in_transit=in_transit,
        delivered=delivered,
        pending=pending
    )

@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    shipment = Shipment.query.get_or_404(id)
    new_status = request.form.get('new_status')
    if new_status:
        shipment.status = new_status
        db.session.commit()
    return redirect(url_for('operations'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
