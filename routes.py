import os
import json
import requests
import google.generativeai as genai
import typing_extensions as typing

from functools import wraps
import requests

from flask import Blueprint, request, session, g, jsonify, redirect
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User, Series, UserInteraction


api = Blueprint("api", __name__)


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


@api.route("/api/search", methods=["GET"])
@login_required
def search():
    query = request.args.get("q")

    res = requests.get(
        "https://api.tvmaze.com/search/shows",
        params={"q": query},
        timeout=10,
    )
    res.raise_for_status()

    return jsonify(res.json()), 200


@api.route("/api/rate", methods=["POST"])
def rate():
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

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
    image = show.get("image") or {}
    summary = show.get("summary")

    if not tvmaze_id or not title:
        raise ValueError("Missing required show data: id or name")

    series = Series.query.get(tvmaze_id)

    if not series:
        series = Series(
            tvmaze_id=tvmaze_id,
            title=title,
            image_url=image.get("medium") or image.get("original"),
            summary=summary,
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

    interactions = []
    if user:
        interactions = UserInteraction.query.filter_by(user_id=user.id).all()

    # Case A
    if not user or not interactions:
        try:
            res = requests.get("https://api.tvmaze.com/shows", timeout=10)
            if res.status_code == 200:
                shows = res.json()
                shows.sort(key=lambda x: x.get('weight', 0), reverse=True)
                return jsonify({"results": shows[:8]}), 200 
            else:
                return jsonify({"error": "Failed to fetch popular shows"}), res.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"TVmaze network error: {str(e)}"}), 500
    #Case B
    liked = []
    neutral = []
    disliked = []
    interested = []
    not_interested = []
    exclude_titles = [] 
    
    for interaction in interactions:
        series_title = interaction.series.title 
        exclude_titles.append(series_title)
        
        if interaction.status == "0":
            liked.append(series_title)
        elif interaction.status == "1":
            neutral.append(series_title)
        elif interaction.status == "2":
            disliked.append(series_title)
        elif interaction.status == "3":
            interested.append(series_title)
        elif interaction.status == "4":
            not_interested.append(series_title)

    prompt = "Tu es un expert en séries TV. Un utilisateur a les préférences suivantes:\n"
    prompt += f"- Séries qu'il ADORE : {', '.join(liked) if liked else 'Aucune'}\n"
    prompt += f"- Séries MOYENNES : {', '.join(neutral) if neutral else 'Aucune'}\n"
    prompt += f"- Séries qu'il DÉTESTE : {', '.join(disliked) if disliked else 'Aucune'}\n"
    prompt += f"- Séries qui l'INTÉRESSENT : {', '.join(interested) if interested else 'Aucune'}\n"
    prompt += f"- Séries qui NE l'INTÉRESSENT PAS : {', '.join(not_interested) if not_interested else 'Aucune'}\n"
    
    prompt += f"\nIMPORTANT : NE RECOMMANDE SURTOUT PAS les séries suivantes car l'utilisateur les connaît déjà : {', '.join(exclude_titles)}.\n"
    
    prompt += "En te basant sur ces goûts, recommande 12 nouvelles séries télévisées. Retourne UNIQUEMENT les titres originaux en anglais."

    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
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
                    final_results.append(tvmaze_data) 
        except requests.exceptions.RequestException:
            continue

    return jsonify({"results": final_results}), 200