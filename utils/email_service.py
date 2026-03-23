import pyotp
from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

# ─── OTP ────────────────────────────────────────────────────────────────────

def generate_otp_secret():
    return pyotp.random_base32()

def get_totp(secret):
    return pyotp.TOTP(secret, interval=300)  # 5 minutes

def generate_otp(secret):
    return get_totp(secret).now()

def verify_otp(secret, otp):
    return get_totp(secret).verify(otp)

# ─── Email Verification Tokens ───────────────────────────────────────────────

def generate_verification_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='email-verify')

def verify_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='email-verify', max_age=expiration)
        return email, None
    except SignatureExpired:
        return None, 'expired'
    except BadSignature:
        return None, 'invalid'

# ─── Password Reset Tokens ────────────────────────────────────────────────────

def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')

def verify_reset_token(token, expiration=600):  # 10 minutes
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=expiration)
        return email, None
    except SignatureExpired:
        return None, 'expired'
    except BadSignature:
        return None, 'invalid'

# ─── Real Email Sending via Flask-Mail ────────────────────────────────────────

def send_email(to_email, subject, body):
    from app import mail
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        print(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print("EMAIL ERROR:", e)
        return False

def send_verification_email(user_email):
    token = generate_verification_token(user_email)
    
    # Use url_for as requested to generate the full link
    # This will use the domain/IP from the request context
    verify_url = current_app.config["BASE_URL"] + url_for('auth_bp.verify_email', token=token)
    subject = "Verify Your Email - STUDENT NATION"
    body = f"""Hello,

Thank you for registering on STUDENT NATION.

Please click the link below to verify your email address:

{verify_url}

If the link above doesn't work, copy and paste it into your browser.

This link will expire in 1 hour.

If you did not create an account, please ignore this email.

-- STUDENT NATION Team
Santhiram Engineering College (Autonomous)
"""
    return send_email(user_email, subject, body)

def send_otp_email(user_email, otp):
    subject = "Your Login OTP - STUDENT NATION"
    body = f"""Hello,

Your One-Time Login Password (OTP) is:

  {otp}

This OTP is valid for 5 minutes only.

If you did not attempt to login, please change your password immediately.

-- STUDENT NATION Team
"""
    return send_email(user_email, subject, body)

def send_password_reset_email(user_email):
    token = generate_reset_token(user_email)
    
    # Use url_for for reset links as well
    reset_url = current_app.config["BASE_URL"] + url_for('auth_bp.reset_password', token=token)
    
    subject = "Password Reset Request - STUDENT NATION"
    body = f"""Hello,

We received a request to reset your password for your STUDENT NATION account.

Click the link below to reset your password:

{reset_url}

If the link above doesn't work, copy and paste it into your browser.

This link will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

-- STUDENT NATION Team
"""
    return send_email(user_email, subject, body)
