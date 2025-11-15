import os
from flask import Flask, request, jsonify, send_from_directory, redirect, session, Response, stream_with_context
from flask_cors import CORS
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import stripe
from models import db, User, Payment, Referral, EmailLead, DomainRental, PaymentCharge, SubscriptionCharge
from dotenv import load_dotenv
from admin_ai_bot import process_admin_command, process_admin_command_streaming
from namecheap_client import NamecheapClient
import json

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET', 'dev-secret-key-change-in-production')

db.init_app(app)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')

serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

PROMO_ACTIVE = os.getenv('PROMO_ACTIVE', 'true').lower() == 'true'
PROMO_PRICE = 20

PACKAGE_PRICES = {
    'basic': {'name': 'Starter', 'price': PROMO_PRICE if PROMO_ACTIVE else 29, 'regular_price': 29, 'stripe_price_id': 'price_basic'},
    'starter': {'name': 'Pro', 'price': PROMO_PRICE if PROMO_ACTIVE else 99, 'regular_price': 99, 'stripe_price_id': 'price_starter'},
    'professional': {'name': 'Elite', 'price': PROMO_PRICE if PROMO_ACTIVE else 249, 'regular_price': 249, 'stripe_price_id': 'price_professional'},
    'empire': {'name': 'Empire', 'price': PROMO_PRICE if PROMO_ACTIVE else 499, 'regular_price': 499, 'stripe_price_id': 'price_empire'}
}

SITE_OWNER_USERNAME = os.getenv('SITE_OWNER_USERNAME', 'rizzosai')

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    host = request.host.lower()
    if 'sales.' in host:
        response = send_from_directory('static', 'claim-domain.html')
    else:
        response = send_from_directory('static', 'email-capture.html')

    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/domain-entry')
def domain_entry():
    response = send_from_directory('static', 'domain-entry.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/packages')
def packages():
    response = send_from_directory('static', 'packages.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/claim-domain')
def claim_domain_page():
    response = send_from_directory('static', 'claim-domain.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/privacy-policy.html')
def privacy_policy():
    response = send_from_directory('static', 'privacy-policy.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/terms-of-service.html')
def terms_of_service():
    response = send_from_directory('static', 'terms-of-service.html')
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/backoffice-coey')
def backoffice_coey():
    return send_from_directory('.', 'backoffice_coey.html')

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    try:
        all_users = User.query.all()
        verified_users = User.query.filter_by(email_verified=True).all()
        all_payments = Payment.query.filter_by(status='completed').all()
        all_referrals = Referral.query.all()

        total_revenue = sum(p.amount for p in all_payments)

        return jsonify({
            'total_users': len(all_users),
            'verified_users': len(verified_users),
            'total_revenue': total_revenue,
            'active_referrals': len(all_referrals)
        })
    except Exception as e:
        return jsonify({
            'total_users': 0,
            'verified_users': 0,
            'total_revenue': 0,
            'active_referrals': 0
        })

@app.route('/api/claude/chat', methods=['POST'])
def claude_chat():
    try:
        from coey_agent import coey

        data = request.json
        message = data.get('message', '')
        context = data.get('context', '')

        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Use the full AI agent with tools
        result = coey.chat(message, context)
        return jsonify(result)

    except Exception as e:
        print(f"Coey AI error: {str(e)}")
        # Intelligent fallback
        message_lower = data.get('message', '').lower()

        if 'user' in message_lower or 'stat' in message_lower:
            stats = admin_stats().get_json()
            response = f"You currently have {stats['total_users']} total users with {stats['verified_users']} verified. Focus on increasing email verification rates to boost engagement!"
        elif 'revenue' in message_lower or 'money' in message_lower:
            stats = admin_stats().get_json()
            response = f"Your total revenue is ${stats['total_revenue']}. To increase this, focus on user acquisition and promoting your affiliate program."
        elif 'growth' in message_lower or 'tip' in message_lower:
            response = "Top growth tips: 1) Leverage your unique 2nd-referral pass-up system, 2) Create urgency with limited offers, 3) Optimize email verification flow, 4) Use social proof, 5) Focus on affiliate engagement."
        else:
            response = "I'm Coey, your AI assistant! I can help with user stats, revenue analysis, growth strategies, and platform insights. What would you like to know?"

        return jsonify({'response': response})

@app.route('/<username>')
def affiliate_link(username):
    user = User.query.filter_by(username=username.lower(), email_verified=True).first()
    if user:
        return redirect(f'/packages?ref={username}')
    return redirect('/')

@app.route('/api/packages', methods=['GET'])
def get_packages():
    return jsonify({
        'packages': [
            {'id': 'basic', 'name': 'Starter', 'price': PACKAGE_PRICES['basic']['price'], 'regular_price': PACKAGE_PRICES['basic']['regular_price'], 'daily_rate': PACKAGE_PRICES['basic']['price'], 'promo_active': PROMO_ACTIVE},
            {'id': 'starter', 'name': 'Pro', 'price': PACKAGE_PRICES['starter']['price'], 'regular_price': PACKAGE_PRICES['starter']['regular_price'], 'daily_rate': PACKAGE_PRICES['starter']['price'], 'promo_active': PROMO_ACTIVE},
            {'id': 'professional', 'name': 'Elite', 'price': PACKAGE_PRICES['professional']['price'], 'regular_price': PACKAGE_PRICES['professional']['regular_price'], 'daily_rate': PACKAGE_PRICES['professional']['price'], 'promo_active': PROMO_ACTIVE},
            {'id': 'empire', 'name': 'Empire', 'price': PACKAGE_PRICES['empire']['price'], 'regular_price': PACKAGE_PRICES['empire']['regular_price'], 'daily_rate': PACKAGE_PRICES['empire']['price'], 'promo_active': PROMO_ACTIVE}
        ]
    })

@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        package_id = data.get('package_id')
        referrer_username = data.get('referrer')

        if package_id not in PACKAGE_PRICES:
            return jsonify({'error': 'Invalid package'}), 400

        package = PACKAGE_PRICES[package_id]

        base_url = os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0]
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{package['name']} - Domain Package",
                        'description': f"${package['price']} RizzosAI Domain Package with Training Guides"
                    },
                    'unit_amount': package['price'] * 100,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{base_url}/register-complete?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/",
            metadata={
                'package_id': package_id,
                'package_price': str(package['price']),
                'referrer_username': referrer_username or ''
            }
        )

        return jsonify({'checkout_url': session.url, 'session_id': session.id})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register_user():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        session_id = data.get('session_id')
        username = data.get('username', '').strip().lower()
        email = data.get('email', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        domain_name = data.get('domain_name', '').strip().lower()
        referrer_username = data.get('referrer')

        if not all([session_id, username, email, full_name]):
            return jsonify({'error': 'All fields are required'}), 400

        if len(username) < 3 or not username.isalnum():
            return jsonify({'error': 'Username must be at least 3 characters and alphanumeric'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400

        if not stripe.api_key:
            return jsonify({'error': 'Payment system not configured'}), 500

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except Exception as stripe_error:
            if 'InvalidRequestError' in str(type(stripe_error).__name__):
                return jsonify({'error': 'Invalid payment session'}), 400
            raise

        if session.payment_status != 'paid':
            return jsonify({'error': 'Payment not completed'}), 400

        existing_payment = Payment.query.filter_by(stripe_session_id=session_id).first()
        if existing_payment:
            return jsonify({'error': 'This payment has already been used'}), 400

        if not session.metadata:
            return jsonify({'error': 'Invalid payment session metadata'}), 400
        package_id = session.metadata.get('package_id', 'basic')
        package = PACKAGE_PRICES.get(package_id, PACKAGE_PRICES['basic'])

        paid_price_str = session.metadata.get('package_price')
        if paid_price_str:
            paid_price = float(paid_price_str)
            expected_amount = int(paid_price * 100)
        else:
            paid_price = package['price']
            expected_amount = package['price'] * 100

        if session.amount_total is None or session.amount_total != expected_amount:
            return jsonify({'error': 'Payment amount mismatch'}), 400

        user = User(  # type: ignore
            username=username,
            email=email,
            full_name=full_name,
            domain_name=domain_name if domain_name else None,
            package_tier=package_id,
            daily_rate=paid_price if paid_price > 0 else package['price'],
            email_verified=False,
            created_at=datetime.utcnow()
        )

        db.session.add(user)
        db.session.flush()

        payment = Payment(  # type: ignore
            user_id=user.id,
            stripe_session_id=session_id,
            amount=(session.amount_total or 0) / 100,
            package_tier=package_id,
            payment_date=datetime.utcnow(),
            status='completed'
        )
        db.session.add(payment)

        if referrer_username:
            referrer = User.query.filter_by(username=referrer_username.lower(), email_verified=True).first()
            if referrer:
                referral_count = Referral.query.filter_by(referrer_id=referrer.id).count()
                referral_order = referral_count + 1

                actual_referrer = referrer
                pass_up = False

                if referral_order == 2:
                    site_owner = User.query.filter_by(username=SITE_OWNER_USERNAME.lower()).first()
                    if site_owner and site_owner.id != referrer.id:
                        actual_referrer = site_owner
                        pass_up = True
                        referrer.pass_up_used = True
                        print(f"\n🎯 PASS-UP ACTIVATED: {referrer.username}'s REFERRAL #{referral_order} ({user.username}) → PASSED UP TO SITE OWNER ({SITE_OWNER_USERNAME})!\n")
                    else:
                        print(f"\n⚠️ PASS-UP FAILED: Site owner '{SITE_OWNER_USERNAME}' not found or referrer is owner\n")
                else:
                    print(f"\n✅ DIRECT REFERRAL: {referrer.username}'s REFERRAL #{referral_order} ({user.username}) → CREDITED TO {referrer.username}\n")

                referral = Referral(  # type: ignore
                    referrer_id=actual_referrer.id,
                    referred_id=user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(referral)

        db.session.commit()

        verification_token = serializer.dumps(email, salt='email-verification')

        send_verification_email(email, full_name, username, verification_token)

        return jsonify({
            'success': True,
            'message': 'Registration successful! Please check your email to verify your account.',
            'username': username
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verification', max_age=86400)

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.email_verified:
            return jsonify({'message': 'Email already verified'}), 200

        user.email_verified = True
        user.verified_at = datetime.utcnow()
        db.session.commit()

        return redirect('/dashboard?verified=true')

    except SignatureExpired:
        return jsonify({'error': 'Verification link expired'}), 400
    except BadSignature:
        return jsonify({'error': 'Invalid verification link'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    try:
        users = User.query.filter_by(email_verified=True).all()

        leaderboard_data = []
        for user in users:
            try:
                referrals_count = Referral.query.filter_by(referrer_id=user.id).count()

                earnings = (user.daily_rate or 0) * max(referrals_count, 1)

                leaderboard_data.append({
                    'name': user.full_name or user.username or 'Unknown',
                    'username': user.username or 'unknown',
                    'earnings': earnings,
                    'referrals': referrals_count,
                    'tier': user.package_tier or 'unknown'
                })
            except Exception as user_error:
                print(f"Error processing user {getattr(user, 'id', 'unknown')}: {str(user_error)}")
                continue

        leaderboard_data.sort(key=lambda x: x['earnings'], reverse=True)

        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data[:50]
        })

    except Exception as e:
        print(f"Leaderboard error: {str(e)}")
        return jsonify({'success': True, 'leaderboard': []}), 200

@app.route('/api/user/<username>', methods=['GET'])
def get_user_stats(username):
    try:
        user = User.query.filter_by(username=username.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if not user.email_verified:
            return jsonify({'error': 'Email not verified'}), 403

        referrals = Referral.query.filter_by(referrer_id=user.id).all()
        referral_list = []

        for ref in referrals:
            referred_user = User.query.get(ref.referred_id)
            if referred_user:
                referral_list.append({
                    'username': referred_user.username,
                    'name': referred_user.full_name,
                    'joined': ref.created_at.isoformat(),
                    'tier': referred_user.package_tier
                })

        total_earnings = user.daily_rate * max(len(referrals), 1)

        return jsonify({
            'success': True,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
            'package_tier': user.package_tier,
            'daily_rate': user.daily_rate,
            'email_verified': user.email_verified,
            'onboarding_completed': user.onboarding_completed,
            'created_at': user.created_at.isoformat(),
            'affiliate_link': f"https://sales.rizzosai.com/{user.username}",
            'total_referrals': len(referrals),
            'total_earnings': total_earnings,
            'referrals': referral_list
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/complete-onboarding/<username>', methods=['POST'])
def complete_onboarding(username):
    try:
        user = User.query.filter_by(username=username.lower()).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user.onboarding_completed = True
        db.session.commit()

        return jsonify({'success': True, 'message': 'Onboarding completed!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/claim-domain', methods=['POST'])
def claim_domain():
    try:
        import requests
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        domain = data.get('domain', '').strip().lower()
        email = data.get('email', '').strip()

        if not domain or not email:
            return jsonify({'error': 'Domain and email are required'}), 400

        api_user = os.getenv('NAMECHEAP_API_USER')
        api_key = os.getenv('NAMECHEAP_API_KEY')
        username = os.getenv('NAMECHEAP_USERNAME')
        forwarded_for = request.headers.get('X-Forwarded-For', request.remote_addr)
        client_ip = (forwarded_for or '127.0.0.1').split(',')[0].strip()

        if not all([api_user, api_key, username]):
            return jsonify({'error': 'Namecheap API not configured'}), 500

        api_url = 'https://api.namecheap.com/xml.response'
        params = {
            'ApiUser': api_user,
            'ApiKey': api_key,
            'UserName': username,
            'ClientIp': client_ip,
            'Command': 'namecheap.domains.check',
            'DomainList': domain
        }

        response = requests.get(api_url, params=params, timeout=10)

        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            available = root.find(".//{http://api.namecheap.com/xml.response}DomainCheckResult")
            if available is not None and available.get('Available') == 'true':
                return jsonify({
                    'success': True,
                    'message': f'Great news! {domain} is available!',
                    'domain': domain,
                    'email': email,
                    'available': True
                })
            else:
                return jsonify({
                    'success': True,
                    'message': f'{domain} is already registered. Try another domain!',
                    'domain': domain,
                    'email': email,
                    'available': False
                })
        else:
            return jsonify({'error': 'Domain check failed. Please try again.'}), 500

    except Exception as e:
        print(f"Domain claim error: {str(e)}")
        return jsonify({'error': 'Unable to process request. Please try again later.'}), 500

@app.route('/api/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print(f"Payment completed for session: {session['id']}")

        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')

            if subscription_id:
                domain_rental = DomainRental.query.filter_by(
                    stripe_subscription_id=subscription_id
                ).first()

                if domain_rental:
                    subscription_charge = SubscriptionCharge(  # type: ignore
                        user_id=domain_rental.user_id,
                        domain_rental_id=domain_rental.id,
                        stripe_subscription_id=subscription_id,
                        stripe_invoice_id=invoice['id'],
                        amount=invoice['amount_paid'] / 100,
                        billing_period_start=datetime.fromtimestamp(invoice['period_start']),
                        billing_period_end=datetime.fromtimestamp(invoice['period_end']),
                        status='paid',
                        payment_date=datetime.utcnow()
                    )
                    db.session.add(subscription_charge)

                    domain_rental.rental_status = 'active'
                    domain_rental.rent_expires_at = datetime.fromtimestamp(invoice['period_end'])

                    db.session.commit()
                    print(f"✅ Subscription payment recorded for domain: {domain_rental.domain_name}")

        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            subscription_id = invoice.get('subscription')

            if subscription_id:
                domain_rental = DomainRental.query.filter_by(
                    stripe_subscription_id=subscription_id
                ).first()

                if domain_rental:
                    subscription_charge = SubscriptionCharge(  # type: ignore
                        user_id=domain_rental.user_id,
                        domain_rental_id=domain_rental.id,
                        stripe_subscription_id=subscription_id,
                        stripe_invoice_id=invoice['id'],
                        amount=invoice['amount_due'] / 100,
                        status='failed',
                        payment_date=datetime.utcnow()
                    )
                    db.session.add(subscription_charge)

                    domain_rental.rental_status = 'payment_failed'

                    db.session.commit()
                    print(f"❌ Subscription payment FAILED for domain: {domain_rental.domain_name}")

        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            subscription_id = subscription['id']

            domain_rental = DomainRental.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()

            if domain_rental:
                domain_rental.rental_status = 'cancelled'

                namecheap = NamecheapClient()
                hold_result = namecheap.hold_domain(domain_rental.domain_name)

                if hold_result.get('success'):
                    domain_rental.registrar_status = 'on_hold'
                    print(f"🔒 Domain {domain_rental.domain_name} put on hold after subscription cancellation")

                db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        print(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 400

def send_verification_email(email, full_name, username, token):
    base_url = os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0]
    if not base_url.startswith('http'):
        base_url = f'https://{base_url}'

    verification_url = f"{base_url}/api/verify-email/{token}"

    print(f"\n{'='*60}")
    print(f"VERIFICATION EMAIL FOR: {email}")
    print(f"Name: {full_name}")
    print(f"Username: {username}")
    print(f"Verification URL: {verification_url}")
    print(f"{'='*60}\n")

def send_domain_welcome_email(email, full_name, domain_name, username):
    base_url = os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0]
    if not base_url.startswith('http'):
        base_url = f'https://{base_url}'

    dashboard_url = f"{base_url}/dashboard"
    affiliate_url = f"https://sales.rizzosai.com/{username}"

    print(f"\n{'='*80}")
    print(f"🎉 DOMAIN REGISTRATION SUCCESS - WELCOME EMAIL")
    print(f"{'='*80}")
    print(f"TO: {email}")
    print(f"NAME: {full_name}")
    print(f"DOMAIN: {domain_name}")
    print(f"")
    print(f"Subject: Welcome! Your Domain {domain_name} is Ready 🚀")
    print(f"")
    print(f"Hi {full_name},")
    print(f"")
    print(f"Congratulations! Your domain {domain_name} has been successfully registered")
    print(f"and your 7-Day Freedom Pass is now ACTIVE!")
    print(f"")
    print(f"YOUR ACCOUNT DETAILS:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✓ Email: {email}")
    print(f"✓ Username: {username}")
    print(f"✓ Domain: {domain_name}")
    print(f"✓ Dashboard: {dashboard_url}")
    print(f"✓ Your Affiliate Link: {affiliate_url}")
    print(f"")
    print(f"WHAT'S NEXT:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"1. Access your dashboard: {dashboard_url}")
    print(f"2. Share your affiliate link to start earning: {affiliate_url}")
    print(f"3. Every referral pays you $20/day!")
    print(f"4. Your daily $20 rental subscription is now active")
    print(f"")
    print(f"IMPORTANT:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"• Your 7-Day Freedom Pass gives you full access")
    print(f"• Domain rental: $20/day (billed daily)")
    print(f"• Refer others and they pay YOUR rental fees!")
    print(f"")
    print(f"Questions? Reply to this email or contact support.")
    print(f"")
    print(f"Welcome to RizzosAI! 🎯")
    print(f"{'='*80}\n")

# Admin routes
@app.route('/domain-setup-guide.html')
def domain_setup_guide():
    return send_from_directory('static', 'domain-setup-guide.html')

@app.route('/backoffice.html')
def backoffice():
    return send_from_directory('static', 'backoffice.html')

@app.route('/admin-dashboard.html')
def admin_dashboard():
    return send_from_directory('static', 'admin-dashboard.html')

@app.route('/api/login', methods=['POST'])
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    username = data.get('username')
    password = data.get('password')

    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'rizzosai2025')

    if username == admin_username and password == admin_password:
        token = serializer.dumps({'admin': True, 'username': username})
        return jsonify({'success': True, 'token': token})

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/admin/dashboard', methods=['GET'])
def get_admin_dashboard():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        data = serializer.loads(token, max_age=86400)  # 24 hour expiry
        if not data.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 401
    except (BadSignature, SignatureExpired):
        return jsonify({'error': 'Invalid or expired token'}), 401

    all_users = User.query.order_by(User.created_at.desc()).all()
    verified_users = User.query.filter_by(email_verified=True).all()
    all_payments = Payment.query.filter_by(status='completed').all()
    all_referrals = Referral.query.all()
    recent_signups = User.query.order_by(User.created_at.desc()).limit(10).all()

    total_revenue = sum(p.amount for p in all_payments)

    users_data = []
    for user in all_users:
        referrals = Referral.query.filter_by(referrer_id=user.id).all()
        referred_users = [User.query.get(r.referred_id) for r in referrals if User.query.get(r.referred_id)]
        referrals_earning = [r for r in referred_users if r and not r.pass_up_used]

        total_earnings = len(referrals_earning) * user.daily_rate

        users_data.append({
            'username': user.username,
            'email': user.email,
            'domain_name': user.domain_name,
            'package_tier': user.package_tier,
            'daily_rate': user.daily_rate,
            'referral_count': len(referrals),
            'total_earnings': total_earnings,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat()
        })

    recent_signups_data = [{
        'username': user.username,
        'package_tier': user.package_tier,
        'created_at': user.created_at.isoformat()
    } for user in recent_signups]

    return jsonify({
        'stats': {
            'total_users': len(all_users),
            'verified_users': len(verified_users),
            'total_revenue': total_revenue,
            'active_referrals': len(all_referrals)
        },
        'users': users_data,
        'recent_signups': recent_signups_data
    })

@app.route('/api/admin/ai-insights', methods=['POST'])
def get_ai_insights():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        data = serializer.loads(token, max_age=86400)  # 24 hour expiry
        if not data.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 401
    except (BadSignature, SignatureExpired):
        return jsonify({'error': 'Invalid or expired token'}), 401

    try:
        from openai import OpenAI
        # the newest OpenAI model is "gpt-5" which was released August 7, 2025.
        # do not change this unless explicitly requested by the user
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        stats = data.get('stats', {})

        prompt = f"""As a business analyst, provide brief insights (2-3 sentences) for this affiliate marketing platform:

Total Users: {stats.get('total_users', 0)}
Verified Users: {stats.get('verified_users', 0)}
Total Revenue: ${stats.get('total_revenue', 0)}
Active Referrals: {stats.get('active_referrals', 0)}

Focus on growth trends, conversion rates, and actionable recommendations."""

        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are a business intelligence assistant providing concise, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=200
        )

        insights = response.choices[0].message.content
        return jsonify({'insights': insights})

    except Exception as e:
        return jsonify({'insights': f'AI insights temporarily unavailable. Error: {str(e)}'})

@app.route('/admin')
def admin_panel():
    return send_from_directory('static', 'admin-panel.html')

@app.route('/api/admin/chat', methods=['POST'])
def admin_chat():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        token_data = serializer.loads(token, max_age=86400)
        if not token_data.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 401
    except (BadSignature, SignatureExpired):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])

        if not user_message:
            return jsonify({'error': 'Message is required'}), 400

        def generate():
            try:
                for chunk in process_admin_command_streaming(user_message, conversation_history):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return Response(stream_with_context(generate()), content_type='text/event-stream')
    except Exception as e:
        return jsonify({'error': f'Failed to process command: {str(e)}'}), 500

@app.route('/api/admin/status', methods=['GET'])
def admin_status():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401

    token = auth_header.split(' ')[1]
    try:
        token_data = serializer.loads(token, max_age=86400)
        if not token_data.get('admin'):
            return jsonify({'error': 'Unauthorized'}), 401
    except (BadSignature, SignatureExpired):
        return jsonify({'error': 'Invalid or expired token'}), 401

    render_configured = bool(os.getenv('RENDER_API_KEY'))
    namecheap_configured = bool(os.getenv('NAMECHEAP_API_KEY') and os.getenv('NAMECHEAP_API_USER'))

    return jsonify({
        'render_configured': render_configured,
        'namecheap_configured': namecheap_configured,
        'openai_configured': bool(os.getenv('OPENAI_API_KEY'))
    })

@app.route('/api/capture-email', methods=['POST'])
def capture_email():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        email = data.get('email', '').strip().lower()

        if not email or '@' not in email:
            return jsonify({'error': 'Valid email is required'}), 400

        existing = EmailLead.query.filter_by(email=email).first()
        if not existing:
            lead = EmailLead(email=email, source='freedom_pass_sales')  # type: ignore
            db.session.add(lead)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Email captured successfully',
            'redirect': '/domain-entry'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit-domain', methods=['POST'])
def submit_domain():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        domain = data.get('domain', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()

        if not domain or not full_name or not email:
            return jsonify({'error': 'Domain, email, and full name are required'}), 400

        session['pending_domain'] = domain
        session['pending_full_name'] = full_name
        session['pending_email'] = email

        return jsonify({
            'success': True,
            'message': 'Domain info saved! Creating payment session...',
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-domain-availability', methods=['POST'])
def check_domain_availability():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400

        domain = data.get('domain', '').strip().lower()

        if not domain:
            return jsonify({'error': 'Domain name is required'}), 400

        if not domain.endswith('.com'):
            domain += '.com'

        existing_rental = DomainRental.query.filter_by(domain_name=domain).first()
        if existing_rental:
            return jsonify({
                'available': False,
                'message': f'{domain} is already registered in our system'
            })

        namecheap = NamecheapClient()
        check_result = namecheap.check_domain_availability(domain)

        if not check_result.get('success'):
            return jsonify({
                'error': 'Unable to check domain availability. Please try again.',
                'details': check_result.get('error', 'Unknown error')
            }), 500

        available = check_result.get('available', False)

        return jsonify({
            'available': available,
            'domain': domain,
            'message': f'{domain} is available!' if available else f'{domain} is already taken'
        })

    except Exception as e:
        return jsonify({
            'error': 'Failed to check domain availability',
            'details': str(e)
        }), 500

@app.route('/api/create-domain-checkout', methods=['POST'])
def create_domain_checkout():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        domain = data.get('domain', '').strip().lower()
        email = data.get('email', '').strip().lower()
        full_name = data.get('full_name', '').strip()
        referrer_username = data.get('referrer', '').strip().lower()

        if not domain or not email or not full_name:
            return jsonify({'error': 'All fields are required'}), 400

        if not domain.endswith('.com'):
            domain += '.com'

        existing_rental = DomainRental.query.filter_by(domain_name=domain).first()
        if existing_rental:
            return jsonify({
                'error': f'{domain} is already registered in our system'
            }), 400

        namecheap = NamecheapClient()
        check_result = namecheap.check_domain_availability(domain)

        if not check_result.get('success') or not check_result.get('available'):
            return jsonify({
                'error': f'{domain} is not available for registration'
            }), 400

        base_url = os.getenv('REPLIT_DOMAINS', 'http://localhost:5000').split(',')[0]
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Domain Registration: {domain}',
                        'description': f'Initial $20 payment for {domain} registration + Daily $20 rental starts immediately'
                    },
                    'unit_amount': 2000,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{base_url}/domain-setup-guide.html?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/domain-entry",
            customer_email=email,
            metadata={
                'domain_name': domain,
                'email': email,
                'full_name': full_name,
                'payment_type': 'domain_initial',
                'referrer_username': referrer_username or ''
            }
        )

        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-domain-payment', methods=['POST'])
def process_domain_payment():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        session_id = data.get('session_id')

        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400

        stripe_session = stripe.checkout.Session.retrieve(session_id)

        if stripe_session.payment_status != 'paid':
            return jsonify({'error': 'Payment not completed'}), 400

        existing_charge = PaymentCharge.query.filter_by(stripe_session_id=session_id).first()
        if existing_charge:
            return jsonify({'error': 'Payment already processed'}), 400

        if not stripe_session.metadata:
            return jsonify({'error': 'Invalid payment session metadata'}), 400
        domain_name = stripe_session.metadata.get('domain_name')
        email = stripe_session.metadata.get('email')
        full_name = stripe_session.metadata.get('full_name')
        referrer_username = stripe_session.metadata.get('referrer_username', '')

        if not domain_name or not email or not full_name:
            return jsonify({'error': 'Missing payment metadata'}), 400

        namecheap = NamecheapClient()

        check_result = opensrs.check_domain_availability(domain_name)
        if not check_result.get('success') or not check_result.get('available'):
            return jsonify({
                'error': f'Domain {domain_name} is not available for registration'
            }), 400

        registration_result = namecheap.register_domain(domain_name, email, full_name)

        if not registration_result.get('success'):
            return jsonify({
                'error': 'Domain registration failed. Please contact support.',
                'details': registration_result.get('error', 'Unknown error')
            }), 500

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(  # type: ignore
                username=domain_name.split('.')[0],
                email=email,
                full_name=full_name,
                package_tier='freedom_pass',
                daily_rate=20,
                email_verified=True,
                freedom_pass_activated=True,
                domain_name=domain_name,
                created_at=datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()

        if referrer_username:
            referrer = User.query.filter_by(username=referrer_username.lower(), email_verified=True).first()
            if referrer:
                referral_count = Referral.query.filter_by(referrer_id=referrer.id).count()
                referral_order = referral_count + 1

                actual_referrer = referrer
                passed_up = False
                pass_up_recipient_id = None

                if referral_order == 2:
                    site_owner = User.query.filter_by(username=SITE_OWNER_USERNAME.lower()).first()
                    if site_owner and site_owner.id != referrer.id:
                        actual_referrer = site_owner
                        passed_up = True
                        pass_up_recipient_id = site_owner.id
                        referrer.pass_up_used = True
                        print(f"\n🎯 DOMAIN RENTAL PASS-UP: {referrer.username}'s REFERRAL #{referral_order} ({user.username}) → PASSED UP TO {SITE_OWNER_USERNAME}!\n")
                    else:
                        print(f"\n⚠️ PASS-UP FAILED: Site owner '{SITE_OWNER_USERNAME}' not found or referrer is owner\n")
                else:
                    print(f"\n✅ DOMAIN RENTAL REFERRAL: {referrer.username}'s REFERRAL #{referral_order} ({user.username}) → CREDITED TO {referrer.username}\n")

                referral = Referral(  # type: ignore
                    referrer_id=actual_referrer.id,
                    referred_id=user.id,
                    referral_order=referral_order,
                    passed_up=passed_up,
                    pass_up_recipient=pass_up_recipient_id,
                    commission_amount=20.00,
                    created_at=datetime.utcnow()
                )
                db.session.add(referral)

        payment_charge = PaymentCharge(  # type: ignore
            user_id=user.id,
            stripe_session_id=session_id,
            amount=20.00,
            charge_type='domain_initial',
            domain_name=domain_name,
            status='completed',
            payment_date=datetime.utcnow()
        )
        db.session.add(payment_charge)

        subscription = stripe.Subscription.create(
            customer=str(stripe_session.customer) if stripe_session.customer else '',
            items=[{
                'price_data': {
                    'currency': 'usd',
                    'product': 'prod_domain_rental',
                    'recurring': {
                        'interval': 'day',
                        'interval_count': 1
                    },
                    'unit_amount': 2000,
                }
            }],
            metadata={
                'domain_name': domain_name,
                'user_id': user.id
            }
        )

        domain_rental = DomainRental(  # type: ignore
            user_id=user.id,
            domain_name=domain_name,
            registrar_status='registered',
            rental_status='active',
            opensrs_order_id=registration_result.get('order_id'),
            stripe_subscription_id=subscription.id,
            rent_started_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.session.add(domain_rental)

        promotion_end = os.getenv('PROMOTION_END_DATE')
        if promotion_end:
            user.freedom_pass_expires = datetime.fromisoformat(promotion_end)
        else:
            user.freedom_pass_expires = datetime.utcnow() + timedelta(days=7)

        db.session.commit()

        send_domain_welcome_email(email, full_name, domain_name, user.username)

        return jsonify({
            'success': True,
            'message': f'Success! {domain_name} registered and daily rental activated.',
            'domain': domain_name,
            'user_id': user.id,
            'subscription_id': subscription.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/live-signups', methods=['GET'])
def live_signups():
    try:
        recent_users = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).order_by(User.created_at.desc()).limit(10).all()

        signups = []
        for user in recent_users:
            time_ago = datetime.utcnow() - user.created_at
            minutes_ago = int(time_ago.total_seconds() / 60)

            if minutes_ago < 1:
                time_str = "Just now"
            elif minutes_ago < 60:
                time_str = f"{minutes_ago} min ago"
            else:
                hours_ago = int(minutes_ago / 60)
                time_str = f"{hours_ago} hour{'s' if hours_ago > 1 else ''} ago"

            initials = ''.join([word[0].upper() for word in user.full_name.split()[:2]])
            signups.append({
                'name': f"{initials}.",
                'time': time_str,
                'package': user.package_tier.capitalize()
            })

        total_24h = len(recent_users)
        total_7d = User.query.filter(
            User.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()

        return jsonify({
            'signups': signups,
            'count_24h': total_24h,
            'count_7d': total_7d
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/promotion-config', methods=['GET'])
def promotion_config():
    try:
        promotion_end = os.getenv('PROMOTION_END_DATE')

        if not promotion_end:
            default_end = datetime.utcnow() + timedelta(days=7)
            promotion_end = default_end.isoformat()

        return jsonify({
            'promotion_end_date': promotion_end,
            'promotion_active': True,
            'price': 20,
            'original_value': 499
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
