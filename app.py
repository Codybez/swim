from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask import render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import bcrypt
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.sql import func
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  # Needed for flashing messages

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fishydatabase.db'  # or any other database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # optional, to avoid warnings

db = SQLAlchemy(app)



s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# Folder to store uploaded profile pictures
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

migrate = Migrate(app, db)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Gmail SMTP server
app.config['MAIL_PORT'] = 587  # TLS port
app.config['MAIL_USE_TLS'] = True  # Use TLS encryption
app.config['MAIL_USE_SSL'] = False  # Don't use SSL
app.config['MAIL_USERNAME'] = 'cdbeznec@gmail.com'  # Your Gmail address
app.config['MAIL_PASSWORD'] = 'kasj zobe daiw rdkj'  # Your Gmail password (or app-specific password if 2FA is enabled)
app.config['MAIL_DEFAULT_SENDER'] = 'cdbeznec@gmail.com'  # The default sender for emails

mail = Mail(app)

# Make sure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic Info
    first_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    
    # Auth Info
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
    # Verification
    is_verified = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.first_name} ({self.email})>'

class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preferred_gender = db.Column(db.String(50), nullable=False)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=False)
    interests = db.Column(db.String(200))  # Store as a comma-separated string or use a relationship for more complex data
    bio = db.Column(db.Text)
    images = db.Column(db.JSON)
    latitude = db.Column(db.Float)   # for geo filtering
    longitude = db.Column(db.Float)
    radius_km = db.Column(db.Integer)

    user = db.relationship('User', backref='preferences')  # One-to-one relationship with User

    def __repr__(self):
        return f'<Preferences {self.id}>'

class UserImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    position = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship('User', backref='images', lazy=True)

@app.route('/')
def index():
    return render_template('index.html')  # You can make a basic homepage or redirect


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        gender = request.form['gender']
        birthday = request.form['birthday']
        email = request.form['email']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


        birthday = datetime.strptime(birthday, '%Y-%m-%d').date()

        # Create user but set verified=False
        user = User(
            first_name=first_name,
            gender=gender,
            birthday=birthday,
            email=email,
            password=password,
            is_verified=False
        )
        db.session.add(user)
        db.session.commit()

        # Generate token
        token = s.dumps(email, salt='email-confirm')

        # Send email
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('email_confirmation.html', confirm_url=confirm_url)
        msg = Message("Confirm Your Email", sender="cdbeznec@gmail.com", recipients=[email])
        msg.html = html
        mail.send(msg)

        flash('A confirmation email has been sent. Please check your inbox.', 'success')
        return redirect(url_for('login'))
    
    # For GET request, show the signup form
    return render_template('signup.html')

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except Exception:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.is_verified:
        flash('Account already verified. Please login.', 'success')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Email confirmed. You can now log in.', 'success')

    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session['user_id'] = user.id

            # Check if preferences are missing
            if not user.preferences:
                return redirect(url_for('preferences'))

            return redirect(url_for('dashboard'))  # Change to your actual logged-in landing page
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if request.method == 'POST':
        # Get data from the form
        preferred_gender = request.form['preferred_gender']
        min_age = request.form['min_age']
        max_age = request.form['max_age']
        interests = request.form['interests']
        bio = request.form['bio']
        radius_km = request.form['radius']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        images = request.files.getlist('images[]')

        image_paths = []
        for image in images:
            if image:
                filename = secure_filename(image.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(file_path)
                image_paths.append(file_path)

        # Create or update preferences for the user
        if user.preferences:
            # If preferences already exist, update them
            user.preferences.preferred_gender = preferred_gender
            user.preferences.min_age = min_age
            user.preferences.max_age = max_age
            user.preferences.interests = interests
            user.preferences.bio = bio
            radius_km=int(radius_km),
            latitude=float(latitude),
            longitude=float(longitude)
            user.preferences.images = image_paths
        else:
            # If no preferences, create a new preferences record
            new_preferences = Preferences(
                user_id=user.id,
                preferred_gender=preferred_gender,
                min_age=min_age,
                max_age=max_age,
                interests=interests,
                bio=bio,
                radius_km=radius_km,
                latitude=latitude,
                longitude=longitude,
                images=image_paths

            )
            db.session.add(new_preferences)

        db.session.commit()  # Save the changes to the database

        return redirect(url_for('dashboard'))  # Redirect after saving preferences

    return render_template('preferences.html')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/preferences/images', methods=['GET', 'POST'])
def manage_images():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if request.method == 'POST':
        images = request.files.getlist('images[]')
        captions = request.form.getlist('captions[]')
        positions = request.form.getlist('positions[]')

        for i, image in enumerate(images):
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)

                new_image = UserImage(
                    user_id=user_id,
                    image_url=filepath,
                    caption=captions[i] if i < len(captions) else '',
                    position=int(positions[i]) if i < len(positions) else i
                )
                db.session.add(new_image)

        db.session.commit()
        return redirect(url_for('manage_images'))

    images = UserImage.query.filter_by(user_id=user_id).order_by(UserImage.position).all()
    return render_template('preferences_images.html', images=images)


def haversine(lat1, lon1, lat2, lon2):
    # Earth radius in km
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


from datetime import datetime

def calculate_age(birthday):
    today = datetime.today()
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    current_prefs = Preferences.query.filter_by(user_id=user_id).first()
    if not current_prefs:
        return redirect(url_for('preferences'))

    min_age = current_prefs.min_age
    max_age = current_prefs.max_age
    preferred_gender = current_prefs.preferred_gender

    other_prefs = Preferences.query.filter(Preferences.user_id != user_id).all()
    nearby_profiles = []

    for pref in other_prefs:
        # Check location data
        if pref.latitude is not None and pref.longitude is not None:
            distance = haversine(
                current_prefs.latitude, current_prefs.longitude,
                pref.latitude, pref.longitude
            )

            if distance <= current_prefs.radius_km:
                # Access related user's birthday and gender
                if pref.user and pref.user.birthday:
                    age = calculate_age(pref.user.birthday)

                    # Check age and gender preferences
                    if min_age <= age <= max_age:
                        if preferred_gender == "Any" or pref.user.gender == preferred_gender:
                            nearby_profiles.append(pref)

    return render_template('dashboard.html', profiles=nearby_profiles)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)  
