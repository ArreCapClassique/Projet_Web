from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    quota_used = db.Column(db.Integer, default=0, nullable=False)
    quota_max = db.Column(db.Integer, default=100, nullable=False)

    def consume_quota(self, amount=1):
        if self.quota_used + amount > self.quota_max:
            return False
        self.quota_used += amount
        db.session.commit()
        return True

    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
