
import requests
import json
import random

from flask import Flask, jsonify, Response, render_template, request, session
from models import Session, Pokemon
from pokemon_data import *

# ----------------------------------------------------------------------------
# Flask setup
# ----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "super_secret_key"


# ----------------------------------------------------------------------------
# Routes
# ----------------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/pokemon/<name>')
def get_pokemon(name):
    data = get_or_cache_pokemon(name)
    if not data:
        return "Pokémon not found", 404

    sprites = extract_sprites(data)
    types = extract_types(data)
    stats = extract_stats(data)
    moves = extract_moves(data)

    return render_template(
        'pokemon.html',
        name=name,
        sprites=sprites,
        types=types,
        stats=stats,
        moves=moves
    )

@app.route('/game/rank')
def pokemon_ranker():
    use_shiny = request.args.get("shiny") == "on"
    pokemon_list = []

    for _ in range(7):
        poke_id = get_random_pokemon_id()
        data = fetch_pokemon(poke_id)
        if data:
            sprite_url = data["sprites"]["front_shiny"] if use_shiny else data["sprites"]["front_default"]
            pokemon_list.append({"name": data["name"], "sprite": sprite_url})

    return render_template('rank.html', pokemon_list=pokemon_list)

@app.route('/game/statsguess')
def pokemon_stats_guess():
    poke_id = get_random_pokemon_id()
    data = fetch_pokemon(poke_id)
    if not data:
        return "Error fetching Pokémon data", 500

    species = fetch_species(data["species"]["url"])
    clues = build_clues(data, species)

    return render_template(
        "statsguess.html",
        clues=clues,
        sprite=data["sprites"]["front_default"],
        name=data["name"]
    )

@app.route('/game/shadowsprite')
def pokemon_dark_sprite_guess():
    poke_id = get_random_pokemon_id()
    data = fetch_pokemon(poke_id)
    if not data:
        return "Error fetching Pokémon data", 500

    return render_template(
        "shadowsprite.html",
        sprite_url=data["sprites"]["front_default"],
        name=data["name"]
    )

@app.route('/game/higherlower', methods=["GET", "POST"])
def pokemon_higher_lower():
    result = None

    # Handle guess
    if request.method == "POST":
        choice = request.form["choice"]
        name2, sprite_url2, stats2 = session["previous"]
        name, sprite_url, stats, stat_choice = session["current_round"]

        left_value = stats2[stat_choice]
        right_value = stats[stat_choice]

        if (choice == "left" and left_value >= right_value) or \
           (choice == "right" and right_value >= left_value):
            result = f"✅ Correct! {stat_choice.capitalize()} values: {left_value} vs {right_value}"
            session["previous"] = (name2, sprite_url2, stats2) if choice == "left" else (name, sprite_url, stats)
        else:
            result = f"❌ Wrong! {stat_choice.capitalize()} values: {left_value} vs {right_value}"
            new_data = fetch_pokemon(get_random_pokemon_id())
            session["previous"] = (
                new_data["name"],
                new_data["sprites"]["front_default"],
                extract_stats(new_data)
            )

    # Prepare left (previous)
    name2, sprite_url2, stats2 = session["previous"]

    # Generate right
    data = fetch_pokemon(get_random_pokemon_id())
    name = data["name"]
    sprite_url = data["sprites"]["front_default"]
    stats = extract_stats(data)

    stat_choice = random.choice(list(stats.keys()))
    session["current_round"] = (name, sprite_url, stats, stat_choice)

    return render_template(
        "higherlower.html",
        name=name, sprite_url=sprite_url, stats=stats,
        name2=name2, sprite_url2=sprite_url2, stats2=stats2,
        stat_choice=stat_choice,
        result=result
    )

@app.route('/game/guessfromid')
def pokemon_guess_from_id():
    poke_id = get_random_pokemon_id()
    data = fetch_pokemon(poke_id)
    name = data["name"]
    sprite_url = data["sprites"]["front_default"]
    return render_template('guessfromid.html',name=name, id=poke_id,sprite_url=sprite_url)

@app.route('/game/rankrandom', methods=["GET", "POST"])
def pokemon_rank_from_id():
    db = Session()

    if request.method == "POST":
        name = request.form["name"]
        score = int(request.form["score"])

        rank_entry = db.query(PokemonRank).filter_by(name=name).first()

        if rank_entry:
            # UPDATE existing
            old_score = rank_entry.score
            rank_entry.score = score
            db.commit()
            result = f"🔄 Updated ranking for {name.title()}: old {old_score}, new {score}"
        else:
            # INSERT new
            new_rank = PokemonRank(name=name, score=score)
            db.add(new_rank)
            db.commit()
            result = f"⭐ New ranking saved for {name.title()}: {score}"

        sprite_url = request.form["sprite_url"]
        return render_template("rankrandom.html", name=name, sprite_url=sprite_url, rank=score, result=result)

    # GET → new random Pokémon
    poke_id = get_random_pokemon_id()
    data = fetch_pokemon(poke_id)
    name = data["name"]
    sprite_url = data["sprites"]["front_default"]

    rank_entry = db.query(PokemonRank).filter_by(name=name).first()
    rank = rank_entry.score if rank_entry else None

    return render_template("rankrandom.html", name=name, sprite_url=sprite_url, rank=rank, result=None)

@app.route('/rankings')
def show_all_rankings():
    db = Session()
    # grab all Pokémon sorted by ID
    pokemon_list = db.query(Pokemon).order_by(Pokemon.id).all()
    rank_map = {r.name: r.score for r in db.query(PokemonRank).all()}

    result = []
    for p in pokemon_list:
        result.append({
            "id": p.id,
            "name": p.name,
            "sprite_url": p.sprite_url,
            "score": rank_map.get(p.name)
        })

    return render_template("allrankings.html", pokemon_list=result)

@app.route("/update_score", methods=["POST"])
def update_score():
    db = Session()
    data = request.get_json()
    name = data["name"]
    score = int(data["score"])

    rank_entry = db.query(PokemonRank).filter_by(name=name).first()
    if rank_entry:
        rank_entry.score = score
    else:
        rank_entry = PokemonRank(name=name, score=score)
        db.add(rank_entry)

    db.commit()
    return {"success": True, "name": name, "score": score}

@app.route('/leaderboard')
def show_leaderboard():
    db = Session()
    ranked = (
        db.query(Pokemon, PokemonRank.score)
        .join(PokemonRank, Pokemon.name == PokemonRank.name)
        .order_by(PokemonRank.score.desc())
        .all()
    )

    result = [
        {"id": p.id, "name": p.name, "sprite_url": p.sprite_url, "score": score}
        for p, score in ranked
    ]

    return render_template("allrankings.html", pokemon_list=result)

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
