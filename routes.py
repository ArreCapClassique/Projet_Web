import json
import os
from functools import wraps

import requests
import typing_extensions as typing
from flask import Blueprint, g, jsonify, request, session
from google import genai
from google.genai import types
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db
from models import Series, User, UserInteraction

api = Blueprint("api", __name__)

PLACEHOLDER_IMAGE = "https://static.tvmaze.com/images/no-img/no-img-portrait-text.png"


def login_required(f):
    """
    session uniquement

    grace à la variable g.user, on peut accéder à l'utilisateur connecté
    dans les fonctions de route protégées par ce décorateur
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("username") is None:
            return {"error": "non autorisé"}, 401

        user = User.get_by_username(session["username"])
        if user is None:
            session.clear()
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


def get_user_status(user_id, tvmaze_id):
    interaction = UserInteraction.query.filter_by(
        user_id=user_id, tvmaze_id=tvmaze_id
    ).first()
    return interaction.status if interaction else None


@api.route("/api/search", methods=["GET"])
def search():
    query = request.args.get("q")
    res = requests.get(
        "https://api.tvmaze.com/search/shows",
        params={"q": query},
        timeout=10,
    )
    res.raise_for_status()
    results = res.json()

    user = None
    username = session.get("username")

    if username:
        user = User.get_by_username(username)

    user_id = user.id if user else None

    for item in results:
        show = item.get("show", {})
        img = show.get("image") or {}

        show["image"] = img.get("medium") or PLACEHOLDER_IMAGE
        show["user_status"] = get_user_status(user_id, show.get("id"))

    return jsonify(results), 200


@api.route("/api/rate", methods=["POST"])
@login_required
def rate():
    data = request.get_json(silent=True) or {}

    show = data.get("show")
    status = data.get("status")

    if not show or not status:
        return jsonify({"error": "Missing show or status"}), 400

    user = User.get_by_username(session["username"])
    if user is None:
        return jsonify({"error": "User not found"}), 404

    try:
        interaction = save_rating(user.id, show, status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    return jsonify(
        {
            "message": "Status saved successfully",
            "interaction_id": interaction.id,
            "tvmaze_id": interaction.tvmaze_id,
            "status": interaction.status,
        }
    ), 200


def save_rating(user_id, show, status):
    tvmaze_id = show.get("id")
    title = show.get("name")
    image = show.get("image")

    if not tvmaze_id or not title:
        raise ValueError("Missing required show data: id or name")

    series = Series.query.get(tvmaze_id)

    if not series:
        series = Series(
            tvmaze_id=tvmaze_id,
            title=title,
            image_url=image or PLACEHOLDER_IMAGE,
        )
        db.session.add(series)
        db.session.flush()

    interaction = UserInteraction.query.filter_by(
        user_id=user_id,
        tvmaze_id=tvmaze_id,
    ).first()

    if interaction:
        interaction.status = status
    else:
        interaction = UserInteraction(
            user_id=user_id,
            tvmaze_id=tvmaze_id,
            status=status,
        )
        db.session.add(interaction)

    db.session.commit()
    return interaction


##### ROUTE RECOMMANDATION ###


class RecommendationList(typing.TypedDict):
    titles: list[str]


@api.route("/api/recommend", methods=["GET"])
def recommend():
    username = session.get("username")
    user = User.get_by_username(username) if username else None
    user_id = user.id if user else None

    interactions = []
    if user:
        interactions = UserInteraction.query.filter_by(user_id=user.id).all()

    # Case A
    if not user or not interactions:
        try:
            res = requests.get("https://api.tvmaze.com/shows", timeout=10)
            res.raise_for_status()

            shows = res.json()
            shows.sort(key=lambda x: x.get("weight", 0), reverse=True)
            user = None
            username = session.get("username")

            if username:
                user = User.get_by_username(username)

            user_id = user.id if user else None
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"TVmaze network error: {str(e)}"}), 500
    # Case B
    liked = []
    neutral = []
    disliked = []
    interested = []
    not_interested = []
    exclude_titles = []

    for interaction in interactions:
        series_title = interaction.series.title
        exclude_titles.append(series_title)

        match interaction.status:
            case "0":
                liked.append(series_title)
            case "1":
                neutral.append(series_title)
            case "2":
                disliked.append(series_title)
            case "3":
                interested.append(series_title)
            case "4":
                not_interested.append(series_title)

    prompt = "You are an expert in TV series. A user has the following viewing preferences:\n"
    prompt += f"- Series they LOVE: {', '.join(liked) if liked else 'None'}\n"
    prompt += f"- Series they find OKAY: {', '.join(neutral) if neutral else 'None'}\n"
    prompt += f"- Series they DISLIKE: {', '.join(disliked) if disliked else 'None'}\n"
    prompt += f"- Series they are INTERESTED in: {', '.join(interested) if interested else 'None'}\n"
    prompt += f"- Series they are NOT INTERESTED in: {', '.join(not_interested) if not_interested else 'None'}\n"
    prompt += (
        f"\nIMPORTANT: DO NOT recommend the following series because the user already knows them: "
        f"{', '.join(sorted(exclude_titles)) if exclude_titles else 'None'}.\n"
    )
    prompt += "Based on these preferences, recommend 12 new TV series. Return ONLY their original English titles."

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RecommendationList,
            ),
        )
        data = json.loads(response.text)
        recommended_titles = data.get("titles", [])
    except Exception as e:
        return jsonify({"error": f"Erreur lors de la génération IA : {str(e)}"}), 500

    final_results = []
    for title in recommended_titles:
        if len(final_results) >= 8:
            break

        try:
            res = requests.get(
                "https://api.tvmaze.com/singlesearch/shows",
                params={"q": title},
                timeout=10,
            )
            if res.status_code == 200:
                tvmaze_data = res.json()
                if tvmaze_data:
                    img = tvmaze_data.get("image") or {}
                    tvmaze_data["image"] = img.get("medium") or PLACEHOLDER_IMAGE
                    tvmaze_data["user_status"] = (
                        get_user_status(user_id, tvmaze_data["id"]) if user_id else None
                    )
                    final_results.append(tvmaze_data)
        except requests.exceptions.RequestException:
            continue

    for show in final_results:
        show["user_status"] = get_user_status(user_id, show["id"]) if user_id else None

    return jsonify({"results": final_results}), 200
