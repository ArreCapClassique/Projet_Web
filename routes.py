from functools import wraps

from flask import Blueprint, request, session, g, send_file
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User


api = Blueprint("api", __name__)


def login_required(f):
    """
    session uniquement

    grace à la variable g.user, on peut accéder à l'utilisateur connecté
    dans les fonctions de route protégées par ce décorateur
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return {"error": "non autorisé"}, 401

        user = User.get_by_username(session["user"])
        if user is None:
            session.clear()
            return {"error": "non autorisé"}, 401

        g.user = user
        return f(*args, **kwargs)

    return wrapper


def auth_required(f):
    """
    session ou clé API

    grace à la variable g.user, on peut accéder à l'utilisateur connecté
    dans les fonctions de route protégées par ce décorateur
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        user = None

        username = session.get("user")
        if username is not None:
            user = User.get_by_username(username)

        if user is None:
            return {"error": "non autorisé"}, 401

        g.user = user
        return f(*args, **kwargs)

    return wrapper


#######################
##### ROUTE LOGIN #####
#######################


@api.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return {"error": "Username and password are required."}, 400

    user = User.query.filter_by(username=username).first()

    if user is None or not check_password_hash(user.password_hash, password):
        return {"error": "Invalid username or password."}, 401

    session["username"] = user.username
    return {"message": "Login successful!"}, 200


@api.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return {"error": "Username and password are required."}, 400

    if User.query.filter_by(username=username).first() is not None:
        return {"error": "Username already exists."}, 400

    hashed_password = generate_password_hash(password)
    user = User(username=username, password_hash=hashed_password)

    db.session.add(user)
    db.session.commit()

    session["username"] = user.username
    return {"message": "Registration successful!"}, 200


@api.route("/api/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return {"ok": True}


###########################
##### ROUTE DASHBOARD #####
###########################


####################
#### ROUTE APP #####
####################
