from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    interactions = db.relationship('UserInteraction', backref='user', lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship('RecommendationLog', backref='user', lazy=True, cascade="all, delete-orphan")



    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


class Series(db.Model):
    __tablename__ = 'series'

    tvmaze_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(512))
    summary = db.Column(db.Text)
    genres = db.Column(db.String(255))  

    interactions = db.relationship('UserInteraction', backref='series', lazy=True)


class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.tvmaze_id'), nullable=False)
    
    rating = db.Column(db.String(20), nullable=False)

    is_watched = db.Column(db.Boolean, default=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecommendationLog(db.Model):
    __tablename__ = 'recommendation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.tvmaze_id'), nullable=False)
    
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)