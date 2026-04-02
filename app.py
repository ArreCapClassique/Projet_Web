from dotenv import load_dotenv
from flask import Flask, render_template, request, session

from extensions import db, sess
from models import Series, User, UserInteraction
from routes import api, login_required

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY"] = db

db.init_app(app)
sess.init_app(app)

app.register_blueprint(api)

with app.app_context():
    db.create_all()


@app.route("/", methods=["GET"])
@app.route("/home", methods=["GET"])
def home():
    username = session.get("username", None)
    if username is not None:
        return render_template("/home.html", username=username)
    return render_template("/auth.html")


@app.route("/auth")
def auth_page():
    return render_template("/auth.html")


@app.route("/search")
@login_required
def search_page():
    query = (request.args.get("q") or "").strip()
    return render_template("/search.html", query=query)


@app.route("/debug/db")
def debug_db():
    users = User.query.all()
    series = Series.query.all()
    interactions = UserInteraction.query.all()

    return {
        "users": [(u.id, u.username) for u in users],
        "series": [
            {"tvmaze_id": s.tvmaze_id, "title": s.title}
            for s in series
        ],
        "interactions": [
            {"user_id": i.user_id, "series_id": i.tvmaze_id, "statue": i.status}
            for i in interactions
        ],
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
