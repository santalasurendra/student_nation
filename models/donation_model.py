from utils.database import db
from datetime import datetime

class Donation(db.Model):
    __tablename__ = 'donations'
    id = db.Column(db.Integer, primary_key=True)
    donor_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True) # Added for UPI tracking
    screenshot = db.Column(db.String(255), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class FundDistribution(db.Model):
    __tablename__ = 'fund_distributions'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    amount_given = db.Column(db.Float, nullable=False)
    approved_by = db.Column(db.String(100), nullable=False) # Name or ID of admin
    date = db.Column(db.DateTime, default=datetime.utcnow)
