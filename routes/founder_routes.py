from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime
from models.team_model import TeamMember
from models.user_model import User, LoginLog
from models.donation_model import Donation, FundDistribution
from models.request_model import EmergencyRequest
from utils.database import db
from utils.helpers import role_required
import os
from werkzeug.utils import secure_filename

founder_bp = Blueprint('founder_bp', __name__)

# ─── Dashboard ────────────────────────────────────────────────────────────────

@founder_bp.route('/dashboard')
@login_required
@role_required('Founder')
def dashboard():
    total_donations  = db.session.query(db.func.sum(Donation.amount)).scalar() or 0
    students_helped  = FundDistribution.query.count()
    pending_requests = EmergencyRequest.query.filter_by(status="Pending").count()
    active_donors    = Donation.query.count()
    locked_accounts  = User.query.filter_by(is_locked=True).count()
    recent_logs      = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(10).all()
    
    total_users = User.query.count()
    total_requests = EmergencyRequest.query.count()
    donations = Donation.query.all()

    # Use the new premium template if it exists, otherwise fallback
    return render_template(
        "founder/dashboard.html",
        total_donations=total_donations,
        students_helped=students_helped,
        pending_requests=pending_requests,
        active_donors=active_donors,
        locked_accounts=locked_accounts,
        recent_logs=recent_logs,
        total_users=total_users,
        total_requests=total_requests,
        total_amount=total_donations,
        donations=donations
    )

# ─── Security Logs ────────────────────────────────────────────────────────────

@founder_bp.route('/security-logs')
@login_required
@role_required('Founder')
def security_logs():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    query = LoginLog.query.order_by(LoginLog.timestamp.desc())
    if status_filter:
        query = query.filter_by(status=status_filter)
    logs = query.paginate(page=page, per_page=30, error_out=False)
    return render_template('admin/security_logs.html', logs=logs, status_filter=status_filter)

# ─── Locked Accounts Management ───────────────────────────────────────────────

@founder_bp.route('/locked-accounts')
@login_required
@role_required('Founder')
def locked_accounts():
    locked_users = User.query.filter_by(is_locked=True).order_by(User.locked_at.desc()).all()
    return render_template('admin/locked_accounts.html', locked_users=locked_users)

@founder_bp.route('/unlock-account/<int:user_id>', methods=['POST'])
@login_required
@role_required('Founder')
def unlock_account(user_id):
    user = User.query.get_or_404(user_id)
    user.is_locked = False
    user.failed_login_attempts = 0
    user.locked_at = None
    db.session.commit()
    # Write an unlock log
    from models.user_model import LoginLog
    entry = LoginLog(email=user.email, ip_address='System',
                     status='unlocked', reason=f'Manually unlocked by Founder')
    db.session.add(entry)
    db.session.commit()
    flash(f'✅ Account for {user.name} ({user.email}) has been unlocked.', 'success')
    return redirect(url_for('founder_bp.locked_accounts'))

# ─── Team Management ──────────────────────────────────────────────────────────

@founder_bp.route('/team_management', methods=['GET', 'POST'])
@login_required
@role_required('Founder')
def team_management():
    if request.method == 'POST':
        if 'action' in request.form and request.form['action'] == 'add_member':
            name        = request.form.get('name')
            email       = request.form.get('email')
            phone       = request.form.get('phone')
            roll_number = request.form.get('roll_number')
            department  = request.form.get('department')
            role        = request.form.get('role')
            image       = request.files.get('image')
            password    = request.form.get('password')
            
            image_filename = None
            if image and image.filename != '':
                filename = secure_filename(image.filename)
                image.save(os.path.join(current_app.config['TEAM_IMAGES_FOLDER'], filename))
                image_filename = filename
                
            member = TeamMember(name=name, email=email, phone=phone, roll_number=roll_number,
                                department=department, role=role, image=image_filename)
            db.session.add(member)
            
            if role in ['Admin', 'Team Member', 'Founder']:
                from app import bcrypt
                existing_user = User.query.filter_by(email=email).first()
                if not existing_user and password:
                    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                    user = User(name=name, email=email, password=hashed_pw, role=role, email_verified=True)
                    db.session.add(user)
                    
            db.session.commit()
            flash("Team member added successfully.", "success")
            return redirect(url_for('founder_bp.team_management'))

    members = TeamMember.query.order_by(TeamMember.date_added.desc()).all()
    return render_template('admin/team_management.html', members=members)

@founder_bp.route('/remove_member/<int:member_id>', methods=['GET', 'POST'])
@login_required
@role_required('Founder')
def remove_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    if member.role == 'Founder':
        flash("You cannot remove a Founder.", "danger")
        return redirect(url_for('founder_bp.team_management'))
    
    user = User.query.filter_by(email=member.email).first()
    if user:
        db.session.delete(user)
        
    db.session.delete(member)
    db.session.commit()
    flash(f"Team member {member.name} removed successfully.", "success")
    return redirect(url_for('founder_bp.team_management'))
