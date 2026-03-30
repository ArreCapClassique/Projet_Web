from datetime import datetime
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    quota_used = db.Column(db.Integer, default=0, nullable=False)
    quota_max = db.Column(db.Integer, default=100, nullable=False)

    # 关系映射：一个用户有多个交互记录和推荐记录
    interactions = db.relationship('UserInteraction', backref='user', lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship('RecommendationLog', backref='user', lazy=True, cascade="all, delete-orphan")

    def consume_quota(self, amount=1):
        if self.quota_used + amount > self.quota_max:
            return False
        self.quota_used += amount
        db.session.commit()
        return True

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


class Series(db.Model):
    __tablename__ = 'series'
    
    # 使用 TVmaze 的 ID 作为主键，避免重复存储
    tvmaze_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(512))
    summary = db.Column(db.Text)
    genres = db.Column(db.String(255))  # 存储如 "Drama, Sci-Fi" 的字符串

    # 关联到交互表
    interactions = db.relationship('UserInteraction', backref='series', lazy=True)


class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.tvmaze_id'), nullable=False)
    
    # 状态：'aimé', 'neutre', 'n’aime pas'
    rating = db.Column(db.String(20), nullable=False)
    # 根据你的设想，只要选择了以上任一选项，即视为已看 (déjà vu)
    is_watched = db.Column(db.Boolean, default=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecommendationLog(db.Model):
    __tablename__ = 'recommendation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    series_id = db.Column(db.Integer, db.ForeignKey('series.tvmaze_id'), nullable=False)
    
    # 记录推荐生成的时间，方便后续做“多样化”逻辑（如：避开最近3天推荐过的）
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)