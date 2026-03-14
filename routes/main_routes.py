from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from models.donation_model import Donation
from models.request_model import EmergencyRequest
from models.team_model import TeamMember
from utils.database import db
import os
from werkzeug.utils import secure_filename

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    total_donations = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    students_helped_count = EmergencyRequest.query.filter_by(status='Approved').count()
    active_donors_count = db.session.query(Donation.email).distinct().count()
    
    approved_cases = EmergencyRequest.query.filter_by(status='Approved', amount_required=db.func.coalesce(EmergencyRequest.amount_required, 0)).all() # Could add more logic later
    approved_cases = EmergencyRequest.query.filter_by(status='Approved').all()
    top_donors = Donation.query.order_by(Donation.amount.desc()).limit(5).all()
    team_members = TeamMember.query.all()
    
    return render_template('index.html', 
                           total_donations=total_donations,
                           students_helped=students_helped_count,
                           active_donors=active_donors_count,
                           approved_cases=approved_cases,
                           top_donors=top_donors,
                           team_members=team_members)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        amount = request.form.get('amount')
        transaction_id = request.form.get('transaction_id')
        screenshot = request.files.get('screenshot')
        
        screenshot_filename = None
        if screenshot and screenshot.filename != '':
            filename = secure_filename(screenshot.filename)
            screenshot.save(os.path.join(current_app.config['PAYMENT_SCREENSHOTS_FOLDER'], filename))
            screenshot_filename = filename
            
        donation = Donation(donor_name=name, email=email, phone=phone, amount=float(amount), transaction_id=transaction_id, screenshot=screenshot_filename)
        db.session.add(donation)
        db.session.commit()
        
        flash('Donation details submitted successfully. Thank you!', 'success')
        return redirect(url_for('main_bp.donate'))
        
    return render_template('donate.html')

@main_bp.route('/emergency_help', methods=['GET', 'POST'])
def emergency_help():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        roll_number = request.form.get('roll_number')
        department = request.form.get('department')
        phone = request.form.get('phone')
        problem = request.form.get('problem')
        amount_required = request.form.get('amount_required')
        hospital_bill = request.files.get('hospital_bill')
        
        bill_filename = None
        if hospital_bill and hospital_bill.filename != '':
            filename = secure_filename(hospital_bill.filename)
            hospital_bill.save(os.path.join(current_app.config['HOSPITAL_BILLS_FOLDER'], filename))
            bill_filename = filename
            
        new_request = EmergencyRequest(
            student_name=student_name,
            roll_number=roll_number,
            department=department,
            phone=phone,
            problem=problem,
            amount_required=float(amount_required),
            hospital_bill=bill_filename
        )
        db.session.add(new_request)
        db.session.commit()
        
        flash('Emergency request submitted successfully. It will be reviewed soon.', 'success')
        return redirect(url_for('main_bp.emergency_help'))
        
    return render_template('emergency_help.html')

@main_bp.route('/top_donors')
def top_donors():
    donors = Donation.query.order_by(Donation.amount.desc()).all()
    return render_template('top_donors.html', donors=donors)

@main_bp.route('/reports')
def reports():
    return render_template('reports.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')
