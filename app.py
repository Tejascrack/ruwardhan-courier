import random
import string
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tybbaca_project_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courier.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Model
class Shipment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  tracking_id = db.Column(db.String(10), unique=True, nullable=False)
  sender_name = db.Column(db.String(100), nullable=False)
  receiver_name = db.Column(db.String(100), nullable=False)
  receiver_address = db.Column(db.Text, nullable=False)
  status = db.Column(db.String(50), default='Order Booked')


def generate_tracking_id():
  return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


# Routes
@app.route('/')
def index():
  return render_template('index.html')


@app.route('/track', methods=['POST'])
def track():
  track_id = request.form.get('tracking_id', '').strip()
  shipment = Shipment.query.filter_by(tracking_id=track_id).first()
  return render_template(
      'index.html', result=shipment, searched=True, query_id=track_id
  )


@app.route('/book', methods=['GET', 'POST'])
def book():
  if request.method == 'POST':
    tracking_code = generate_tracking_id()
    new_shipment = Shipment(
        tracking_id=tracking_code,
        sender_name=request.form['sender_name'],
        receiver_name=request.form['receiver_name'],
        receiver_address=request.form['receiver_address'],
        status='In Transit',
    )
    db.session.add(new_shipment)
    db.session.commit()
    return render_template('book.html', new_id=tracking_code)
  return render_template('book.html')


@app.route('/calculator')
def calculator():
  return render_template('calculator.html')


@app.route('/operations')
def operations():
  shipments = Shipment.query.order_by(Shipment.id.desc()).all()
  total = len(shipments)
  in_transit = sum(1 for s in shipments if s.status == 'In Transit')
  delivered = sum(1 for s in shipments if s.status == 'Delivered')
  pending = sum(
      1
      for s in shipments
      if s.status in ['Order Booked', 'Pending Pickup', 'Order Received']
  )
  return render_template(
      'operations.html',
      shipments=shipments,
      total=total,
      in_transit=in_transit,
      delivered=delivered,
      pending=pending,
  )


@app.route('/update_status/<int:id>', methods=['POST'])
def update_status(id):
  shipment = Shipment.query.get_or_404(id)
  new_status = request.form.get('new_status')
  if new_status:
    shipment.status = new_status
    db.session.commit()
  return redirect(url_for('operations'))


if __name__ == '__main__':
  with app.app_context():
    db.create_all()
  app.run(debug=True)