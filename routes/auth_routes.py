import time
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User, LoginLog
from utils.database import db
from utils.email_service import (
    generate_otp_secret, generate_otp, verify_otp,
    verify_token, verify_reset_token,
    send_verification_email, send_otp_email, send_password_reset_email
)

auth_bp = Blueprint('auth_bp', __name__)

MAX_LOGIN_ATTEMPTS = 5   # lock after this many consecutive failures

def _log(email, status, reason=None):
    """Write a login attempt to the LoginLog table."""
    ip = request.remote_addr
    entry = LoginLog(email=email, ip_address=ip, status=status, reason=reason)
    db.session.add(entry)
    db.session.commit()


# ─── Login / Register (Tabbed) ────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        action = request.form.get('action')

        # ── SIGN UP ──────────────────────────────────────────────────────────
        if action == 'register':
            from app import bcrypt
            name     = request.form.get('name')
            email    = request.form.get('email')
            phone    = request.form.get('phone')
            password = request.form.get('password')
            confirm  = request.form.get('confirm_password')
            role     = request.form.get('role')

            if role == 'Founder':
                flash('Founder role cannot be created through signup.', 'danger')
                return redirect(url_for('auth_bp.login', tab='signup'))

            if password != confirm:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('auth_bp.login', tab='signup'))

            if User.query.filter_by(email=email).first():
                flash('An account with this email already exists.', 'danger')
                return redirect(url_for('auth_bp.login', tab='signup'))

            hashed_pw  = bcrypt.generate_password_hash(password).decode('utf-8')
            otp_secret = generate_otp_secret()
            new_user   = User(name=name, email=email, phone=phone,
                              password=hashed_pw, role=role,
                              otp_secret=otp_secret, email_verified=False)
            db.session.add(new_user)
            db.session.commit()

            sent = send_verification_email(email)
            if sent:
                flash('Account created! A verification link has been sent to your email.', 'success')
            else:
                flash('Account created, but we could not send the verification email. Contact support.', 'warning')
            return redirect(url_for('auth_bp.login', tab='login'))

        # ── SIGN IN ──────────────────────────────────────────────────────────
        elif action == 'login':
            from app import bcrypt
            email    = request.form.get('email')
            password = request.form.get('password')
            role     = request.form.get('role')

            user = User.query.filter_by(email=email).first()

            # ── Account not found
            if not user:
                _log(email, 'failed', 'Account not found')
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('auth_bp.login'))

            # ── Account locked
            if user.is_locked:
                _log(email, 'locked', 'Login attempt on locked account')
                flash('🔒 Your account has been locked after too many failed attempts. '
                      'Please contact an Admin or the Founder to unlock your account.', 'danger')
                return redirect(url_for('auth_bp.login'))

            # ── Wrong password
            if not bcrypt.check_password_hash(user.password, password):
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                remaining = MAX_LOGIN_ATTEMPTS - user.failed_login_attempts

                if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.is_locked  = True
                    user.locked_at  = datetime.utcnow()
                    db.session.commit()
                    _log(email, 'locked', f'Account locked after {MAX_LOGIN_ATTEMPTS} failed attempts')
                    flash('🔒 Your account has been locked after 5 failed login attempts. '
                          'Please contact an Admin or the Founder to unlock your account.', 'danger')
                else:
                    db.session.commit()
                    _log(email, 'failed', f'Wrong password (attempt {user.failed_login_attempts})')
                    flash(f'Invalid email or password. {remaining} attempt(s) remaining before lockout.', 'danger')
                return redirect(url_for('auth_bp.login'))

            # ── Wrong role
            if user.role != role:
                _log(email, 'failed', f'Wrong role selected: {role} (actual: {user.role})')
                flash(f'You are not an {role}. Please select the correct login role.', 'danger')
                return redirect(url_for('auth_bp.login'))

            # ── Email not verified
            if not user.email_verified:
                _log(email, 'failed', 'Email not verified')
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('auth_bp.login'))

            # ── All checks passed — reset failed attempts
            user.failed_login_attempts = 0
            db.session.commit()

            # Generate & email OTP
            if not user.otp_secret:
                user.otp_secret = generate_otp_secret()
                db.session.commit()

            otp = generate_otp(user.otp_secret)
            
            # Store OTP and expiry in session for verification
            session['otp_code']   = str(otp)
            session['otp_expiry'] = time.time() + 300  # 5 minutes valid

            send_otp_email(email, otp)
            _log(email, 'otp_sent', 'OTP sent — awaiting 2FA verification')

            session['pending_user_id']  = user.id
            session['otp_last_sent']    = time.time()
            session['otp_resend_count'] = 0
            flash('An OTP has been sent to your email. Please verify to continue.', 'info')
            return redirect(url_for('auth_bp.otp_verification'))

    active_tab = request.args.get('tab', 'login')
    return render_template('login.html', active_tab=active_tab)


# ─── OTP Verification ─────────────────────────────────────────────────────────

import time

OTP_RESEND_COOLDOWN = 30   # seconds
OTP_MAX_RESEND     = 5     # max resends per login session

@auth_bp.route('/otp-verification', methods=['GET', 'POST'])
def otp_verification():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth_bp.login'))

    user = User.query.get(session['pending_user_id'])
    if not user:
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        stored_otp  = session.get('otp_code')
        otp_expiry  = session.get('otp_expiry', 0)

        if not entered_otp:
            flash('Please enter the verification code.', 'warning')
        elif time.time() > otp_expiry:
            flash('OTP expired. Click resend OTP.', 'danger')
        elif entered_otp == str(stored_otp):
            # Success: Clear OTP data from session
            session.pop('pending_user_id', None)
            session.pop('otp_last_sent', None)
            session.pop('otp_resend_count', None)
            session.pop('otp_code', None)
            session.pop('otp_expiry', None)

            login_user(user)
            flash('Logged in successfully!', 'success')
            return _redirect_by_role(user)
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    # Calculate resend context for UI
    last_sent     = session.get('otp_last_sent', 0)
    resend_count  = session.get('otp_resend_count', 0)
    now           = time.time()
    cooldown_left = max(0, int(OTP_RESEND_COOLDOWN - (now - last_sent)))
    otp_expiry_left = max(0, int(session.get('otp_expiry', 0) - now))

    return render_template(
        'otp_verification.html',
        cooldown_left=cooldown_left,
        otp_expiry_left=otp_expiry_left,
        resend_count=resend_count,
        max_resend=OTP_MAX_RESEND
    )


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'pending_user_id' not in session:
        return redirect(url_for('auth_bp.login'))

    user = User.query.get(session['pending_user_id'])
    if not user:
        return redirect(url_for('auth_bp.login'))

    now          = time.time()
    last_sent    = session.get('otp_last_sent', 0)
    resend_count = session.get('otp_resend_count', 0)

    if resend_count >= OTP_MAX_RESEND:
        flash('You have exceeded the maximum OTP resend attempts. Please login again.', 'danger')
        # Clear the pending login session and send user back to login
        session.pop('pending_user_id', None)
        session.pop('otp_last_sent', None)
        session.pop('otp_resend_count', None)
        return redirect(url_for('auth_bp.login'))

    if (now - last_sent) < OTP_RESEND_COOLDOWN:
        remaining = int(OTP_RESEND_COOLDOWN - (now - last_sent))
        flash(f'Please wait {remaining} seconds before requesting a new OTP.', 'warning')
        return redirect(url_for('auth_bp.otp_verification'))

    # Generate and send fresh OTP
    otp = generate_otp(user.otp_secret)
    
    # Update stored OTP and expiry
    session['otp_code']   = str(otp)
    session['otp_expiry'] = now + 300 # 5 minutes
    
    sent = send_otp_email(user.email, otp)

    if sent:
        session['otp_last_sent']    = now
        session['otp_resend_count'] = resend_count + 1
        flash(f'A new OTP has been sent to your email. ({resend_count + 1}/{OTP_MAX_RESEND} resends used)', 'info')
    else:
        flash('Failed to send OTP. Please try again.', 'danger')

    return redirect(url_for('auth_bp.otp_verification'))



# ─── Email Verification ───────────────────────────────────────────────────────

@auth_bp.route('/verify-email/<token>')
def verify_email(token):
    email, error = verify_token(token)
    if error == 'expired':
        flash('Verification link expired. Please request a new verification email.', 'danger')
        return redirect(url_for('auth_bp.login'))
    if error == 'invalid' or not email:
        flash('Invalid verification link.', 'danger')
        return redirect(url_for('auth_bp.login'))

    user = User.query.filter_by(email=email).first()
    if user:
        user.email_verified = True
        db.session.commit()
        flash('Your email has been successfully verified. You can now log in.', 'success')
        return redirect(url_for('auth_bp.login'))

    flash('Account not found.', 'danger')
    return redirect(url_for('auth_bp.login'))


# ─── Resend Verification Email ────────────────────────────────────────────────

@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    if request.method == 'POST':
        email = request.form.get('email')
        user  = User.query.filter_by(email=email).first()
        if user and not user.email_verified:
            send_verification_email(email)
        flash('If a matching unverified account was found, a new verification email has been sent.', 'info')
        return redirect(url_for('auth_bp.login'))
    return render_template('resend_verification.html')


# ─── Forgot Password ──────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user  = User.query.filter_by(email=email).first()
        if user:
            send_password_reset_email(email)
        flash('If an account matches that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth_bp.login'))
    return render_template('forgot_password.html')


# ─── Reset Password ───────────────────────────────────────────────────────────

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email, error = verify_reset_token(token)
    if error == 'expired':
        flash('Password reset link has expired (10 minutes). Please request a new one.', 'danger')
        return redirect(url_for('auth_bp.forgot_password'))
    if error == 'invalid' or not email:
        flash('Password reset link is invalid.', 'danger')
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        from app import bcrypt
        password = request.form.get('password')
        confirm  = request.form.get('confirm_password')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(request.url)

        user = User.query.filter_by(email=email).first()
        if user:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            flash('Password successfully changed. You can now log in.', 'success')
            return redirect(url_for('auth_bp.login'))

    return render_template('reset_password.html')


# ─── Logout ───────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_bp.index'))


# ─── Helper ───────────────────────────────────────────────────────────────────

def _redirect_by_role(user):
    if user.role == 'Founder':
        return redirect(url_for('founder_bp.dashboard'))
    elif user.role == 'Admin':
        return redirect(url_for('admin_bp.dashboard'))
    return redirect(url_for('main_bp.index'))
