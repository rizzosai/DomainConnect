from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    domain_name = db.Column(db.String(255), nullable=True)
    package_tier = db.Column(db.String(20), nullable=False)
    daily_rate = db.Column(db.Float, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    pass_up_used = db.Column(db.Boolean, default=False)
    onboarding_completed = db.Column(db.Boolean, default=False)
    freedom_pass_activated = db.Column(db.Boolean, default=False)
    freedom_pass_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    payments = db.relationship('Payment', backref='user', lazy=True)
    referrals_made = db.relationship('Referral', foreign_keys='Referral.referrer_id', backref='referrer', lazy=True)
    referrals_received = db.relationship('Referral', foreign_keys='Referral.referred_id', backref='referred', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_session_id = db.Column(db.String(200), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    package_tier = db.Column(db.String(20), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    
    def __repr__(self):
        return f'<Payment {self.id} - ${self.amount}>'

class Referral(db.Model):
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_order = db.Column(db.Integer, nullable=True)
    pass_up_recipient = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    passed_up = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    commission_paid = db.Column(db.Boolean, default=False)
    commission_amount = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<Referral {self.referrer_id} -> {self.referred_id}>'

class DomainRental(db.Model):
    __tablename__ = 'domain_rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain_name = db.Column(db.String(255), nullable=False, index=True)
    registrar_status = db.Column(db.String(50), default='pending')
    rental_status = db.Column(db.String(50), default='active')
    opensrs_order_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(200), nullable=True)
    rent_started_at = db.Column(db.DateTime, nullable=True)
    rent_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='domain_rentals', lazy=True)
    
    def __repr__(self):
        return f'<DomainRental {self.domain_name} - {self.rental_status}>'

class PaymentCharge(db.Model):
    __tablename__ = 'payment_charges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(200), unique=True, nullable=True)
    stripe_session_id = db.Column(db.String(200), unique=True, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    charge_type = db.Column(db.String(50), default='domain_initial')
    domain_name = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='payment_charges', lazy=True)
    
    def __repr__(self):
        return f'<PaymentCharge {self.id} - ${self.amount} - {self.charge_type}>'

class SubscriptionCharge(db.Model):
    __tablename__ = 'subscription_charges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    domain_rental_id = db.Column(db.Integer, db.ForeignKey('domain_rentals.id'), nullable=True)
    stripe_subscription_id = db.Column(db.String(200), nullable=False, index=True)
    stripe_invoice_id = db.Column(db.String(200), unique=True, nullable=True)
    amount = db.Column(db.Float, nullable=False)
    billing_period_start = db.Column(db.DateTime, nullable=True)
    billing_period_end = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='subscription_charges', lazy=True)
    domain_rental = db.relationship('DomainRental', backref='subscription_charges', lazy=True)
    
    def __repr__(self):
        return f'<SubscriptionCharge {self.id} - ${self.amount} - {self.status}>'

class EnvVault(db.Model):
    __tablename__ = 'env_vault'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    scope = db.Column(db.String(50), default='global')  # global|subdomain|service
    subdomain = db.Column(db.String(255), nullable=True)
    data_encrypted = db.Column(db.Text, nullable=False)
    encrypted = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EnvVault {self.name} (encrypted={self.encrypted})>'

class EmailLead(db.Model):
    __tablename__ = 'email_leads'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    source = db.Column(db.String(50), default='sales_page')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    converted = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<EmailLead {self.email}>'
