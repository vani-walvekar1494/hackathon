from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model, UserMixin):  # Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    last_stock_price = db.Column(db.Float, nullable=True)  # Assuming this column exists now
    is_active = db.Column(db.Boolean, default=True)  # Add is_active attribute here
    
    # Optionally add other fields like date_created, etc.
    
    def __repr__(self):
        return f'<User {self.username}>'




class TradingDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    last_trading_date = db.Column(db.String(20), nullable=False)
