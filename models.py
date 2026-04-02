from datetime import datetime, timezone
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    interactions = db.relationship(
        "UserInteraction", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()


class Series(db.Model):
    __tablename__ = "series"

    tvmaze_id = db.Column(db.Integer, primary_key=True, autoincrement=False)
    title = db.Column(db.String(255), nullable=False)
    image_url = db.Column(db.String(512))

    interactions = db.relationship("UserInteraction", backref="series", lazy=True)


class UserInteraction(db.Model):
    __tablename__ = "user_interactions"
    __table_args__ = (
        db.UniqueConstraint("user_id", "tvmaze_id", name="uq_user_series_interaction"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    tvmaze_id = db.Column(db.Integer, db.ForeignKey("series.tvmaze_id"), nullable=False)

    status = db.Column(
        db.Enum(
            "0", #Like
            "1", #Neutral
            "2", #Dislike
            "3", #Interested
            "4", #Not Interested
        ),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

