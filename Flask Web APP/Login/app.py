from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Extend session lifetime

db = SQLAlchemy(app)
Session(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    if 'username' in session:
        return redirect("https://b18f-103-157-53-200.ngrok-free.app")  # Redirect to the plant disease app
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect("https://b18f-103-157-53-200.ngrok-free.app")  # Redirect after successful login
        else:
            flash('Invalid credentials, please try again.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user:
            flash('Username already exists.')
        else:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful, please log in and Save your password./पंजीकरण सफल, कृपया लॉग इन करें और अपना पासवर्ड सहेजें।')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect('/login')

if __name__ == '__main__':
    create_tables()  # Ensure tables are created before running the app
    app.run(host='0.0.0.0', port=3000, debug=True)  # Listen on all interfaces
