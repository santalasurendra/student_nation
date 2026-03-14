from utils.database import db
from datetime import datetime

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_requests'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    problem = db.Column(db.Text, nullable=False)
    amount_required = db.Column(db.Float, nullable=False)
    amount_received = db.Column(db.Float, default=0.0)
    hospital_bill = db.Column(db.String(255), nullable=True) # filename of uploaded bill
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    date_requested = db.Column(db.DateTime, default=datetime.utcnow)
