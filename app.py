from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, TradingDate  # Import TradingDate here
from forms import LoginForm, SignupForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from flask_mail import Mail, Message
from joblib import load
import numpy as np
from flask_migrate import Migrate

# --- Flask App Config ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
# Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vaniw555@gmail.com'
app.config['MAIL_PASSWORD'] = 'Magenta@18273645'
app.config['MAIL_DEFAULT_SENDER'] = 'vaniw555@gmail.com'  # App password from Google account

mail = Mail(app)
migrate = Migrate(app, db)
# --- Initialize DB and Login ---
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    db.create_all()

# --- Load Prediction Model ---
model = load('revenue_model.pkl')  # Make sure this file exists!

# --- Helper Functions for Stock Data and Email Notification ---
def load_last_trading_date(symbol):
    # Query to get the last trading date for the stock symbol
    entry = TradingDate.query.filter_by(symbol=symbol).first()
    return entry.last_trading_date if entry else None

def save_trading_date(symbol, new_date):
    # Save the new trading date for the stock symbol
    entry = TradingDate.query.filter_by(symbol=symbol).first()
    if entry:
        entry.last_trading_date = new_date
    else:
        entry = TradingDate(symbol=symbol, last_trading_date=new_date)
        db.session.add(entry)
    db.session.commit()

def check_and_notify(stock_data, user_email):
    symbol = stock_data.get('01. symbol')
    latest_date = stock_data.get('07. latest trading day')

    if not symbol or not latest_date:
        return

    last_date = load_last_trading_date(symbol)

    if latest_date != last_date:
        save_trading_date(symbol, latest_date)

        subject = f"📢 New Trading Data: {symbol}"
        body = f"""
Hello!

New trading data is available for {symbol}.

🔹 Price: ${stock_data.get('05. price')}
🔹 Change: {stock_data.get('09. change')} ({stock_data.get('10. change percent')})
🔹 Date: {latest_date}

- CEO Revenue Optimizer Bot
        """

        msg = Message(subject, recipients=[user_email], body=body)
        mail.send(msg)

# --- User Loader ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Landing Page (Public) ---
@app.route('/')
def home():
    return render_template('home.html')

# --- Sign Up ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password, email=form.email.data)
        db.session.add(new_user)
        db.session.commit()
        
        # Send welcome email with stock data
        send_welcome_email(new_user.email)
        
        flash('Account created!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

def send_welcome_email(user_email):
    stock_symbol = 'AAPL'
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    stock_data = {}

    if api_key:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            stock_data = data.get('Global Quote', {})
            price = stock_data.get('05. price', 'N/A')

            # Compose email content
            subject = "Welcome to CEO Revenue Optimizer"
            body = f"Hello, {user_email}!\n\nWelcome to CEO Revenue Optimizer!\nThe current price of {stock_symbol} is ${price}.\nWe will notify you of any significant changes in the stock price."

            # Send email
            msg = Message(subject, recipients=[user_email], body=body)
            mail.send(msg)


# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# --- Logout ---
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# --- Dashboard Page with Live Stock Data ---
@app.route('/dashboard')
@login_required
def dashboard():
    stock_symbol = 'AAPL'  # Default stock
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    stock_data = {}

    if api_key:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock_symbol}&apikey={api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            stock_data = data.get('Global Quote', {})
            current_price = float(stock_data.get('05. price', '0'))

            # Check if the price has changed significantly (e.g., 5%)
            if current_price != 0 and abs(current_price - current_user.last_stock_price) / current_user.last_stock_price >= 0.05:
                # Send email about the change
                send_stock_change_email(current_user.email, current_price)
                
                # Update the last_stock_price
                current_user.last_stock_price = current_price
                db.session.commit()

    return render_template('index.html', stock_data=stock_data)

def send_stock_change_email(user_email, current_price):
    subject = "Significant Stock Price Change"
    body = f"Hello,\n\nThe stock price has changed significantly! The new price is ${current_price}.\nKeep an eye on the market!"
    
    msg = Message(subject, recipients=[user_email], body=body)
    mail.send(msg)


# --- Revenue Prediction Form ---
@app.route('/predict_form')
@login_required
def predict_form():
    return render_template('index.html')

# --- Other Static Pages ---
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/predict', methods=['POST'])
@login_required
def predict_revenue():
    try:
        # Extract data from the form
        marketing_spend = float(request.form['marketing_spend'])
        rnd_investment = float(request.form['rnd_investment'])
        employee_count = int(request.form['employee_count'])
        operational_costs = float(request.form['operational_costs'])
        customer_satisfaction = float(request.form['customer_satisfaction'])
        market_share = float(request.form['market_share'])

        # Prepare the input data for prediction (you may need to reshape or adjust this based on your model)
        features = np.array([[marketing_spend, rnd_investment, employee_count, operational_costs, customer_satisfaction, market_share]])

        # Predict the revenue using your model
        predicted_revenue = model.predict(features)[0]

        # Render the result page with the predicted revenue
        return render_template('result.html', predicted_revenue=predicted_revenue)

    except Exception as e:
        # If there's an error (e.g., missing fields or model prediction failure)
        return render_template('index.html', error_message="An error occurred. Please check your inputs.")


# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)