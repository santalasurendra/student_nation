from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models.donation_model import Donation, FundDistribution
from models.request_model import EmergencyRequest
from utils.database import db
from utils.helpers import role_required

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard')
@login_required
@role_required('Admin', 'Founder', 'Team Member')
def dashboard():
    total_donations = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    students_helped_count = EmergencyRequest.query.filter_by(status='Approved').count()
    pending_requests_count = EmergencyRequest.query.filter_by(status='Pending').count()
    active_donors_count = db.session.query(Donation.email).distinct().count()
    
    return render_template('admin/dashboard.html',
                           total_donations=total_donations,
                           students_helped=students_helped_count,
                           pending_requests=pending_requests_count,
                           active_donors=active_donors_count)

@admin_bp.route('/requests')
@login_required
@role_required('Admin', 'Founder', 'Team Member')
def requests_list():
    requests = EmergencyRequest.query.order_by(EmergencyRequest.date_requested.desc()).all()
    return render_template('admin/requests.html', requests=requests)

@admin_bp.route('/requests/approve/<int:req_id>')
@login_required
@role_required('Admin', 'Founder')
def approve_request(req_id):
    req = EmergencyRequest.query.get_or_404(req_id)
    req.status = 'Approved'
    db.session.commit()
    flash(f"Request for {req.student_name} approved.", 'success')
    return redirect(url_for('admin_bp.requests_list'))

@admin_bp.route('/requests/reject/<int:req_id>')
@login_required
@role_required('Admin', 'Founder')
def reject_request(req_id):
    req = EmergencyRequest.query.get_or_404(req_id)
    req.status = 'Rejected'
    db.session.commit()
    flash(f"Request for {req.student_name} rejected.", 'danger')
    return redirect(url_for('admin_bp.requests_list'))

@admin_bp.route('/donations')
@login_required
@role_required('Admin', 'Founder', 'Team Member')
def donations_list():
    donations = Donation.query.order_by(Donation.date.desc()).all()
    return render_template('admin/donations.html', donations=donations)

@admin_bp.route('/fund_distribution', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Founder')
def fund_distribution():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        amount_given = request.form.get('amount_given')
        
        fd = FundDistribution(student_name=student_name, amount_given=float(amount_given), approved_by=current_user.name)
        db.session.add(fd)
        db.session.commit()
        flash("Fund distribution recorded.", "success")
        return redirect(url_for('admin_bp.fund_distribution'))
        
    distributions = FundDistribution.query.order_by(FundDistribution.date.desc()).all()
    return render_template('admin/fund_distribution.html', distributions=distributions)
