from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paydrive.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app)
migrate = Migrate(app, db)

# Dictionary to store connected users
connected_users = {}

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Profile Model
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(15))
    dob = db.Column(db.String(10))
    gender = db.Column(db.String(10))
    language = db.Column(db.String(20))
    emergency_contact = db.Column(db.String(15))
    picture = db.Column(db.String(100))
    bike_name = db.Column(db.String(50))
    bike_model = db.Column(db.String(50))
    licence = db.Column(db.String(20))
    bike_colour = db.Column(db.String(20))
    bike_number = db.Column(db.String(20))
    role = db.Column(db.String(10))  # rider, offerer, both

# Ride Request Model
class RideRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rider_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    arrival_time = db.Column(db.String(20))
    phone = db.Column(db.String(15))
    rider_preference = db.Column(db.String(10))
    accepted_offer_id = db.Column(db.Integer, db.ForeignKey('ride_offer.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')

# Ride Offer Model
class RideOffer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    address = db.Column(db.String(100))
    location = db.Column(db.String(100))
    arrival_time = db.Column(db.String(20))
    frequent = db.Column(db.String(10))
    bike_name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    bike_model = db.Column(db.String(50))
    licence = db.Column(db.String(20))
    bike_color = db.Column(db.String(20))
    bike_number = db.Column(db.String(20))
    rider_preference = db.Column(db.String(10))
    accepted_request_id = db.Column(db.Integer, db.ForeignKey('ride_request.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')

# Initialize database
with app.app_context():
    db.create_all()

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        connected_users[user_id] = request.sid
        print(f"User {user_id} connected with SID {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    if user_id and user_id in connected_users:
        del connected_users[user_id]
        print(f"User {user_id} disconnected")

# Routes
@app.route('/splash')
def splash():
    redirect_url = url_for('login') if 'user_id' not in session else url_for('dashboard')
    return render_template('splash.html', redirect_url=redirect_url)

@app.route('/')
def index():
    return redirect(url_for('splash'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    recent_requests = RideRequest.query.filter_by(user_id=user.id).order_by(RideRequest.id.desc()).limit(5).all()
    recent_offers = RideOffer.query.filter_by(user_id=user.id).order_by(RideOffer.id.desc()).limit(5).all()
    pending_requests = db.session.query(RideRequest).join(RideOffer, RideRequest.accepted_offer_id == RideOffer.id).filter(
        RideOffer.user_id == user.id, RideRequest.accepted_offer_id != None
    ).all()
    confirmed_rides_as_rider = RideRequest.query.filter_by(user_id=user.id, status='confirmed').order_by(RideRequest.id.desc()).limit(5).all()
    confirmed_rides_as_offerer = RideOffer.query.filter_by(user_id=user.id, status='confirmed').order_by(RideOffer.id.desc()).limit(5).all()
    return render_template('dashboard.html', username=user.username, recent_requests=recent_requests, 
                         recent_offers=recent_offers, pending_requests=pending_requests,
                         confirmed_rides_as_rider=confirmed_rides_as_rider, 
                         confirmed_rides_as_offerer=confirmed_rides_as_offerer)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists')
        else:
            user = User(username=username, password=password, email=email)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/choose', methods=['GET'])
def choose_ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('choose.html')

@app.route('/ride', methods=['POST'])
def ride():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ride_type = request.form['ride_type']
    location = request.form['location']
    rider_preference = request.form['rider_preference']
    session['ride_location'] = location
    session['rider_preference'] = rider_preference
    profile = Profile.query.filter_by(user_id=session['user_id']).first()
    if not profile:
        session['intended_action'] = 'ride'
        session['ride_type'] = ride_type
        flash('Please create a profile before proceeding.')
        return redirect(url_for('profile'))
    if ride_type == 'offer':
        return render_template('ride_offer.html', profile=profile, location=location, rider_preference=rider_preference)
    elif ride_type == 'request':
        return render_template('ride_request.html', profile=profile, location=location, rider_preference=rider_preference)
    flash('Invalid ride type')
    return redirect(url_for('choose_ride'))

@app.route('/submit_offer', methods=['POST'])
def submit_offer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    profile = Profile.query.filter_by(user_id=user.id).first()
    if not profile:
        session['intended_action'] = 'submit_offer'
        flash('Please create a profile before submitting a ride offer.')
        return redirect(url_for('profile'))
    if profile.role in ['offerer', 'both']:
        if not all([request.form.get('bike_name'), request.form.get('bike_model'), 
                    request.form.get('licence'), request.form.get('bike_color'), 
                    request.form.get('bike_number')]):
            flash('All bike details are required for ride offerers.')
            return redirect(url_for('profile'))
    offer = RideOffer(
        user_id=user.id,
        address=request.form['address'],
        location=request.form['location'],
        arrival_time=request.form['arrival_time'],
        frequent=request.form['frequent'],
        bike_name=request.form['bike_name'],
        gender=request.form['gender'],
        phone=request.form['phone'],
        bike_model=request.form['bike_model'],
        licence=request.form['licence'],
        bike_color=request.form['bike_color'],
        bike_number=request.form['bike_number'],
        rider_preference=session.get('rider_preference', 'any'),
        status='pending'
    )
    db.session.add(offer)
    db.session.commit()
    return render_template('rider_confirmation.html', offer=offer)

@app.route('/submit_request', methods=['POST'])
def submit_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    profile = Profile.query.filter_by(user_id=user.id).first()
    if not profile:
        session['intended_action'] = 'submit_request'
        flash('Please create a profile before submitting a ride request.')
        return redirect(url_for('profile'))
    request_data = RideRequest(
        user_id=user.id,
        rider_name=request.form['rider_name'],
        location=request.form['location'],
        arrival_time=request.form['arrival_time'],
        phone=request.form['phone'],
        rider_preference=session.get('rider_preference', 'any'),
        status='pending'
    )
    db.session.add(request_data)
    db.session.commit()
    return render_template('rider_confirmation.html', ride_request=request_data)

@app.route('/confirm_submission/<type>/<int:id>', methods=['POST'])
def confirm_submission(type, id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    if type == 'offer':
        offer = RideOffer.query.get(id)
        if not offer or offer.user_id != user.id:
            flash('Invalid offer or unauthorized access.')
            return redirect(url_for('choose_ride'))
        requests = RideRequest.query.filter_by(location=offer.location, accepted_offer_id=None, status='pending').filter(
            (RideRequest.rider_preference == offer.gender) | (RideRequest.rider_preference == 'any')
        ).all()
        return render_template('match.html', requests=requests, is_offer=True)
    
    elif type == 'request':
        request_data = RideRequest.query.get(id)
        if not request_data or request_data.user_id != user.id:
            flash('Invalid request or unauthorized access.')
            return redirect(url_for('choose_ride'))
        profile = Profile.query.filter_by(user_id=user.id).first()
        query = RideOffer.query.filter_by(
            location=request_data.location,
            accepted_request_id=None,
            status='pending'
        )
        query = query.filter(
            (RideOffer.rider_preference == profile.gender) | (RideOffer.rider_preference == 'any')
        )
        offers = query.order_by(RideOffer.location).all()
        return render_template('ride_matches.html', offers=offers, request_id=request_data.id)
    
    flash('Invalid submission type.')
    return redirect(url_for('choose_ride'))

@app.route('/request_ride/<int:offer_id>', methods=['POST'])
def request_ride(offer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    offer = RideOffer.query.get(offer_id)
    if not offer or offer.accepted_request_id or offer.status != 'pending':
        flash('Ride offer is no longer available.')
        return redirect(url_for('choose_ride'))
    request_data = RideRequest.query.filter_by(user_id=user.id, status='pending').order_by(RideRequest.id.desc()).first()
    if not request_data:
        flash('No active ride request found.')
        return redirect(url_for('choose_ride'))
    offer.accepted_request_id = request_data.id
    request_data.accepted_offer_id = offer.id
    offer.status = 'accepted'
    request_data.status = 'accepted'
    db.session.commit()
    
    offerer_profile = Profile.query.filter_by(user_id=offer.user_id).first()
    return render_template('rider_confirmation.html', offerer=offerer_profile, booking=offer)

@app.route('/confirm_ride/<int:offer_id>', methods=['POST'])
def confirm_ride(offer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    offer = RideOffer.query.get(offer_id)
    if not offer or offer.status != 'accepted':
        flash('Ride offer is not available for confirmation.')
        return redirect(url_for('ride_matches'))
    request_data = RideRequest.query.get(offer.accepted_request_id)
    if not request_data:
        flash('Associated ride request not found.')
        return redirect(url_for('ride_matches'))
    # Allow both rider and offerer to confirm the ride
    if request_data.user_id != user.id and offer.user_id != user.id:
        flash('You are not authorized to confirm this ride.')
        return redirect(url_for('ride_matches'))
    
    offer.status = 'confirmed'
    request_data.status = 'confirmed'
    db.session.commit()
    
    # Notify the other party
    other_user_id = offer.user_id if user.id == request_data.user_id else request_data.user_id
    if other_user_id in connected_users:
        socketio.emit('ride_confirmed', {
            'message': f'Your ride has been confirmed by {"the rider" if user.id == offer.user_id else "the offerer"}!',
            'request_id': request_data.id
        }, room=connected_users[other_user_id])
    
    flash('Ride confirmed successfully!')
    return redirect(url_for('dashboard'))

@app.route('/cancel_acceptance/<int:offer_id>', methods=['POST'])
def cancel_acceptance(offer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    offer = RideOffer.query.get(offer_id)
    if not offer or offer.status != 'accepted':
        flash('Ride offer is not in a state to cancel acceptance.')
        return redirect(url_for('dashboard'))
    request_data = RideRequest.query.get(offer.accepted_request_id)
    if not request_data:
        flash('Associated ride request not found.')
        return redirect(url_for('dashboard'))
    # Check if the user is the rider or offerer
    if offer.user_id != user.id and request_data.user_id != user.id:
        flash('You are not authorized to cancel this ride acceptance.')
        return redirect(url_for('dashboard'))
    
    # Revert statuses to pending
    offer.status = 'pending'
    request_data.status = 'pending'
    offer.accepted_request_id = None
    request_data.accepted_offer_id = None
    db.session.commit()
    
    # Notify the other party if they are online
    other_user_id = offer.user_id if user.id == request_data.user_id else request_data.user_id
    if other_user_id in connected_users:
        socketio.emit('notification', {
            'message': 'The ride acceptance has been canceled by the other party.'
        }, room=connected_users[other_user_id])
    
    flash('Ride acceptance canceled successfully.')
    return redirect(url_for('dashboard'))

@app.route('/ride_matches', methods=['GET'])
def ride_matches():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    profile = Profile.query.filter_by(user_id=user.id).first()
    if not profile:
        session['intended_action'] = 'ride_matches'
        flash('Please create a profile before viewing ride matches.')
        return redirect(url_for('profile'))
    request_data = RideRequest.query.filter_by(user_id=user.id, status='pending').order_by(RideRequest.id.desc()).first()
    if not request_data:
        flash('You have no active ride requests. Create a new request to find matches.')
        return redirect(url_for('choose_ride'))
    query = RideOffer.query.filter_by(
        location=request_data.location,
        accepted_request_id=None,
        status='pending'
    )
    query = query.filter(
        (RideOffer.rider_preference == profile.gender) | (RideOffer.rider_preference == 'any')
    )
    offers = query.order_by(RideOffer.location).all()
    if not offers:
        flash('No matching ride offers found at this time. Check back later or create a new request.')
        return redirect(url_for('dashboard'))
    for offer in offers:
        offer_profile = Profile.query.filter_by(user_id=offer.user_id).first()
        offer.profile_picture = offer_profile.picture if offer_profile and offer_profile.picture and os.path.exists(offer_profile.picture) else url_for('static', filename='images/default_profile.jpg')
    return render_template('ride_matches.html', offers=offers, request_id=request_data.id)

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    request_data = RideRequest.query.get(request_id)
    profile = Profile.query.filter_by(user_id=user.id).first()
    if not profile:
        session['intended_action'] = 'accept_request'
        session['request_id'] = request_id
        flash('Please create a profile before accepting a ride request.')
        return redirect(url_for('profile'))
    query = RideOffer.query.filter_by(
        user_id=user.id,
        location=request_data.location,
        accepted_request_id=None,
        status='pending'
    )
    query = query.filter(
        (RideRequest.rider_preference == profile.gender) | (RideRequest.rider_preference == 'any')
    )
    offer = query.first()
    if offer:
        offer.accepted_request_id = request_id
        request_data.accepted_offer_id = offer.id
        offer.status = 'accepted'
        request_data.status = 'accepted'
        db.session.commit()
        offerer_profile = Profile.query.filter_by(user_id=offer.user_id).first()
        return render_template('rider_confirmation.html', offerer=offerer_profile, booking=offer)
    flash('No matching offer found')
    return redirect(url_for('match'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    profile = Profile.query.filter_by(user_id=user.id).first()
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        language = request.form.get('language')
        emergency_contact = request.form.get('emergency_contact')
        role = request.form.get('role')
        picture = request.files.get('picture')
        picture_path = None
        if picture:
            picture_path = os.path.join('static', 'uploads', picture.filename)
            os.makedirs(os.path.dirname(picture_path), exist_ok=True)
            picture.save(picture_path)
        bike_name = request.form.get('bike_name') if role in ['offerer', 'both'] else None
        bike_model = request.form.get('bike_model') if role in ['offerer', 'both'] else None
        licence = request.form.get('licence') if role in ['offerer', 'both'] else None
        bike_colour = request.form.get('bike_colour') if role in ['offerer', 'both'] else None
        bike_number = request.form.get('bike_number') if role in ['offerer', 'both'] else None
        if profile:
            profile.name = name
            profile.email = email
            profile.phone = phone
            profile.dob = dob
            profile.gender = gender
            profile.language = language
            profile.emergency_contact = emergency_contact
            profile.role = role
            profile.bike_name = bike_name
            profile.bike_model = bike_model
            profile.licence = licence
            profile.bike_colour = bike_colour
            profile.bike_number = bike_number
            if picture_path:
                profile.picture = picture_path
        else:
            profile = Profile(
                user_id=user.id, name=name, email=email, phone=phone, dob=dob,
                gender=gender, language=language, emergency_contact=emergency_contact,
                role=role, picture=picture_path, bike_name=bike_name, bike_model=bike_model,
                licence=licence, bike_colour=bike_colour, bike_number=bike_number
            )
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully')

        intended_action = session.pop('intended_action', None)
        if intended_action == 'ride':
            ride_type = session.pop('ride_type', None)
            location = session.get('ride_location', '')
            rider_preference = session.get('rider_preference', 'any')
            if ride_type == 'offer':
                return render_template('ride_offer.html', profile=profile, location=location, rider_preference=rider_preference)
            elif ride_type == 'request':
                return render_template('ride_request.html', profile=profile, location=location, rider_preference=rider_preference)
            return redirect(url_for('choose_ride'))
        elif intended_action == 'submit_offer':
            location = session.get('ride_location', '')
            rider_preference = session.get('rider_preference', 'any')
            return render_template('ride_offer.html', profile=profile, location=location, rider_preference=rider_preference)
        elif intended_action == 'submit_request':
            location = session.get('ride_location', '')
            rider_preference = session.get('rider_preference', 'any')
            return render_template('ride_request.html', profile=profile, location=location, rider_preference=rider_preference)
        elif intended_action == 'ride_matches':
            request_data = RideRequest.query.filter_by(user_id=user.id, status='pending').order_by(RideRequest.id.desc()).first()
            if not request_data:
                flash('You have no active ride requests. Create a new request to find matches.')
                return redirect(url_for('choose_ride'))
            query = RideOffer.query.filter_by(
                location=request_data.location,
                accepted_request_id=None,
                status='pending'
            )
            query = query.filter(
                (RideOffer.rider_preference == profile.gender) | (RideOffer.rider_preference == 'any')
            )
            offers = query.order_by(RideOffer.location).all()
            if not offers:
                flash('No matching ride offers found at this time. Check back later or create a new request.')
                return redirect(url_for('dashboard'))
            for offer in offers:
                offer_profile = Profile.query.filter_by(user_id=offer.user_id).first()
                offer.profile_picture = offer_profile.picture if offer_profile and offer_profile.picture and os.path.exists(offer_profile.picture) else url_for('static', filename='images/default_profile.jpg')
            return render_template('ride_matches.html', offers=offers, request_id=request_data.id)
        elif intended_action == 'accept_request':
            request_id = session.pop('request_id', None)
            if request_id:
                request_data = RideRequest.query.get(request_id)
                query = RideOffer.query.filter_by(
                    user_id=user.id,
                    location=request_data.location,
                    accepted_request_id=None,
                    status='pending'
                )
                query = query.filter(
                    (RideRequest.rider_preference == profile.gender) | (RideRequest.rider_preference == 'any')
                )
                offer = query.first()
                if offer:
                    offer.accepted_request_id = request_id
                    request_data.accepted_offer_id = offer.id
                    offer.status = 'accepted'
                    request_data.status = 'accepted'
                    db.session.commit()
                    offerer_profile = Profile.query.filter_by(user_id=offer.user_id).first()
                    return render_template('rider_confirmation.html', offerer=offerer_profile, booking=offer)
                flash('No matching offer found')
            return redirect(url_for('match'))
        return redirect(url_for('profile'))

    profile_picture = profile.picture if profile and profile.picture and os.path.exists(profile.picture) else url_for('static', filename='images/default_profile.jpg')
    return render_template('profile.html', profile=profile, profile_picture=profile_picture)

@app.route('/match', methods=['GET'])
def match():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    requests = RideRequest.query.filter_by(user_id=user.id).order_by(RideRequest.id.desc()).all()
    return render_template('match.html', requests=requests, is_offer=False)

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    requests = RideRequest.query.filter_by(user_id=user.id).order_by(RideRequest.id.desc()).all()
    offers = RideOffer.query.filter_by(user_id=user.id).order_by(RideOffer.id.desc()).all()
    return render_template('history.html', requests=requests, offers=offers)

@app.route('/payment', methods=['GET'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')

@app.route('/help', methods=['GET'])
def help():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('help.html')

@app.route('/settings', methods=['GET'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id in connected_users:
        del connected_users[user_id]
    session.pop('user_id', None)
    session.pop('ride_location', None)
    session.pop('rider_preference', None)
    session.pop('intended_action', None)
    session.pop('ride_type', None)
    session.pop('request_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, debug=True)