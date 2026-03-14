from utils.database import db
from datetime import datetime

class TeamMember(db.Model):
    __tablename__ = 'team_members'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
