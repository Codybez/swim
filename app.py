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
from flask_login import current_user, login_required
from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import logout_user
from flask_login import login_user


app = Flask(__name__)

app.secret_key = 'your_secret_key_here'  # Needed for flashing messages

login_manager = LoginManager()  # Create a LoginManager instance
login_manager.init_app(app)  # Initialize it with the app

# Define the user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Replace `User` with your user model


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

class User(db.Model, UserMixin):
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
    image1 = db.Column(db.String(255), nullable=True)
    image2 = db.Column(db.String(255), nullable=True)
    image3 = db.Column(db.String(255), nullable=True)
    image4 = db.Column(db.String(255), nullable=True)
    image5 = db.Column(db.String(255), nullable=True)
    preferred_gender = db.Column(db.String(50), nullable=False)
    min_age = db.Column(db.Integer, nullable=False)
    max_age = db.Column(db.Integer, nullable=False)
    interests = db.Column(db.String(200))  # Store as a comma-separated string or use a relationship for more complex data
    bio = db.Column(db.Text)
    location = db.Column(db.String(50))
    latitude = db.Column(db.Float)   # for geo filtering
    longitude = db.Column(db.Float)
    radius_km = db.Column(db.Integer)

    # New fields added
    star_sign = db.Column(db.String(50), nullable=True)
    mbti_type = db.Column(db.String(10), nullable=True)
    height = db.Column(db.Integer, nullable=True)
    smoking = db.Column(db.String(50), nullable=True)
    drinking = db.Column(db.String(50), nullable=True)
    music_preferences = db.Column(db.String(200), nullable=True)
    fitness = db.Column(db.String(100), nullable=True)
    job_title = db.Column(db.String(100), nullable=True)
    education = db.Column(db.String(100), nullable=True)
    pets = db.Column(db.String(50), nullable=True)
    children = db.Column(db.String(50), nullable=True)
    looking_for = db.Column(db.String(200), nullable=True)

    user = db.relationship('User', backref='preferences')  # One-to-one relationship with User

    def __repr__(self):
        return f'<Preferences {self.id}>'


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
            login_user(user)

            # Check if preferences are missing
            if not user.preferences:
                return redirect(url_for('preferences'))

            return redirect(url_for('dashboard'))  # Change to your actual logged-in landing page
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

from werkzeug.utils import secure_filename
import os


@app.route('/preferences', methods=['GET', 'POST'])
@login_required  # Ensures the user is logged in before accessing this route
def preferences():
    user = current_user  # Get the current logged-in user (Flask-Login handles this)

    if request.method == 'POST':
        # Get data from the form
        preferred_gender = request.form['preferred_gender']
        min_age = request.form['min_age']
        max_age = request.form['max_age']
        interests = request.form['interests']
        bio = request.form['bio']
        location = request.form.get("location")
        radius_km = request.form['radius_km']
        latitude = request.form['latitude']
        longitude = request.form['longitude']

        # Print the form data to the console (Optional for debugging)
        print(f"Preferred Gender: {preferred_gender}")
        print(f"Min Age: {min_age}")
        print(f"Max Age: {max_age}")
        print(f"Interests: {interests}")
        print(f"Bio: {bio}")
        print(f"Radius (km): {radius_km}")
        print(f"Latitude: {latitude}")
        print(f"Longitude: {longitude}")
        print(f"Location: {location}")

        # Process images
        image_paths = {}
        for i in range(1, 6):  # Loop over image1, image2, image3, image4, image5
            image = request.files.get(f'image{i}')  # Get each image field
            if image:
                filename = secure_filename(image.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(file_path)
                image_paths[f'image{i}'] = filename  # Save image to corresponding field

        # Create or update preferences for the user
        if user.preferences:
            # If preferences already exist, update them
            user.preferences.preferred_gender = preferred_gender
            user.preferences.min_age = min_age
            user.preferences.max_age = max_age
            user.preferences.interests = interests
            user.preferences.bio = bio
            user.preferences.location = location
            user.preferences.radius_km = int(radius_km)
            user.preferences.latitude = float(latitude)
            user.preferences.longitude = float(longitude)

            # Update the image fields
            for key, path in image_paths.items():
                setattr(user.preferences, key, path)

        else:
            # If no preferences, create a new preferences record
            new_preferences = Preferences(
                user_id=user.id,  # Use current_user's id
                preferred_gender=preferred_gender,
                min_age=min_age,
                max_age=max_age,
                interests=interests,
                bio=bio,
                location=location,
                radius_km=int(radius_km),
                latitude=float(latitude),
                longitude=float(longitude),
                **image_paths  # Spread the image paths to their corresponding fields (image1, image2, etc.)
            )
            db.session.add(new_preferences)

        try:
            db.session.commit()  # Save the changes to the database
            print("Preferences committed successfully.")
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            print(f"Error committing preferences: {e}")
        
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
    user = current_user
    user_id = user.id 
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
                            # Add the preferences to nearby profiles, including image paths
                            nearby_profiles.append(pref)

    return render_template('dashboard.html', profiles=nearby_profiles, calculate_age=calculate_age, user=user,)

@app.route('/preview-profile/<int:user_id>')
@login_required
def preview_profile(user_id):
    user = User.query.get_or_404(user_id)  # Get user details
    preferences = Preferences.query.filter_by(user_id=user_id).first()  # Get their preferences

    all_preferences = Preferences.query.all()  # If needed in template

    return render_template(
        "profile_modal.html",
        user=user,
        preferences=preferences,
        all_preferences=all_preferences,
        calculate_age=calculate_age  # Pass the age function to the template
    )



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.query.get(current_user.id)
    preferences = Preferences.query.filter_by(user_id=user.id).first()

    if request.method == "POST":
        # Handle image uploads
        for i in range(1, 6):
            image_file = request.files.get(f"image{i}")
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                upload_path = os.path.join("static", "uploads", filename)
                image_file.save(upload_path)
                setattr(preferences, f"image{i}", filename)

        # Update other fields safely
        preferences.bio = request.form.get("bio")
        preferences.location = request.form.get("location")
        preferences.latitude = request.form.get("latitude")
        preferences.longitude = request.form.get("longitude")
        preferences.radius_km = request.form.get("radius_km")
        preferences.interests = request.form.get("interests")
        preferences.preferred_gender = request.form.get("preferred_gender")
        preferences.star_sign = request.form.get("star_sign")
        preferences.mbti_type = request.form.get("mbti_type")
        preferences.height = request.form.get("height")
        preferences.smoking = request.form.get("smoking")
        preferences.drinking = request.form.get("drinking")
        preferences.music_preferences = request.form.get("music_preferences")
        preferences.fitness = request.form.get("fitness")
        preferences.job_title = request.form.get("job_title")
        preferences.education = request.form.get("education")
        preferences.pets = request.form.get("pets")
        preferences.children = request.form.get("children")
        preferences.looking_for = request.form.get("looking_for")

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))

    return render_template("profile.html", user=user, preferences=preferences)

@app.route("/modal/profile/<int:user_id>")
def profile_modal(user_id):
    user = User.query.get_or_404(user_id)  # Get user details
    preferences = Preferences.query.filter_by(user_id=user_id).first()  # Get their preferences

    all_preferences = Preferences.query.all()  # If needed in template

    return render_template(
        "profile_modal.html",
        user=user,
        preferences=preferences,
        all_preferences=all_preferences,
        calculate_age=calculate_age  # Pass the age function to the template
    )

@app.route("/save-preferences", methods=["POST"])
@login_required
def save_preferences():
    preferences = current_user.preferences

    # Save all the fields
    preferences.location = request.form.get("location")
    preferences.latitude = request.form.get("latitude")
    preferences.longitude = request.form.get("longitude")
    preferences.radius_km = request.form.get("radius_km")
    preferences.bio = request.form.get("bio")
    preferences.preferred_gender = request.form.get("preferred_gender")
    preferences.star_sign = request.form.get("star_sign")
    preferences.mbti_type = request.form.get("mbti_type")
    preferences.height = request.form.get("height")
    preferences.smoking = request.form.get("smoking")
    preferences.drinking = request.form.get("drinking")
    preferences.music_preferences = request.form.get("music_preferences")
    preferences.fitness = request.form.get("fitness")
    preferences.job_title = request.form.get("job_title")
    preferences.education = request.form.get("education")
    preferences.pets = request.form.get("pets")
    preferences.children = request.form.get("children")
    preferences.interests = request.form.get('interests', '').strip()

    db.session.commit()
    return "", 204  # Empty response, success

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)  
