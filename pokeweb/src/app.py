
import requests
import json
import random

from flask import Flask, jsonify, Response, render_template, request, session, redirect, url_for
from models import Session, Pokemon, User, PokemonRank
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
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    db = Session()

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        if not username:
            return render_template('login.html', error="Please enter a username.")

        # Check if user exists
        user = db.query(User).filter_by(username=username).first()

        # Create if not found
        if not user:
            user = User(username=username)
            db.add(user)
            db.commit()

        # Store in session
        session['username'] = username

        return redirect(url_for('pokeparty_home'))  # Redirect to your main hub

    return render_template('login.html', error=None)

@app.route('/pokeparty')
def pokeparty_home():
    return render_template('pokeparty.html')

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
    if "previous" not in session:
            # fetch a random Pokémon for the left slot
            poke_id2 = random.randint(1, 1025)
            data2 = requests.get(f'https://pokeapi.co/api/v2/pokemon/{poke_id2}').json()
            session["previous"] = (
                data2["name"],
                data2["sprites"]["front_default"],
                extract_stats(data2),
            )

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

@app.route('/game/typematch', methods=["GET", "POST"])
def type_match_game():
    # Game: show a random type. Player selects all weaknesses (2x from),
    # resistances (0.5x from), immunities (0x from), and strengths (2x to).

    all_types = TYPE_NAMES

    if request.method == "POST":
        type_name = request.form.get("type_name", "").lower()
        picked_weak = set(request.form.getlist("weaknesses"))
        picked_resist = set(request.form.getlist("resist_from"))
        picked_immune = set(request.form.getlist("immune_from"))
        picked_strong = set(request.form.getlist("strengths"))

        matchups = get_type_matchups(type_name)
        correct_weak = set(matchups.get("weak_to", set()))
        correct_resist = set(matchups.get("resist_from", set()))
        correct_immune = set(matchups.get("immune_from", set()))
        correct_strong = set(matchups.get("strong_against", set()))

        result = {
            "type": type_name,
            "picked_weak": sorted(picked_weak),
            "picked_resist": sorted(picked_resist),
            "picked_immune": sorted(picked_immune),
            "picked_strong": sorted(picked_strong),
            "correct_weak": sorted(correct_weak),
            "correct_resist": sorted(correct_resist),
            "correct_immune": sorted(correct_immune),
            "correct_strong": sorted(correct_strong),
            "weak_missed": sorted(correct_weak - picked_weak),
            "weak_extra": sorted(picked_weak - correct_weak),
            "resist_missed": sorted(correct_resist - picked_resist),
            "resist_extra": sorted(picked_resist - correct_resist),
            "immune_missed": sorted(correct_immune - picked_immune),
            "immune_extra": sorted(picked_immune - correct_immune),
            "strong_missed": sorted(correct_strong - picked_strong),
            "strong_extra": sorted(picked_strong - correct_strong),
        }

        return render_template(
            'typematch.html',
            mode='result',
            all_types=all_types,
            result=result,
        )

    # GET: present a random type and blank form
    type_name = random.choice(TYPE_NAMES)
    return render_template(
        'typematch.html',
        mode='play',
        type_name=type_name,
        all_types=all_types,
    )

@app.route('/game/rankrandom', methods=["GET", "POST"])
def pokemon_rank_from_id():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = Session()
    user = db.query(User).filter_by(username=session['username']).first()

    if request.method == "POST":
        name = request.form["name"]
        score = int(request.form["score"])

        rank_entry = db.query(PokemonRank).filter_by(name=name, user_id=user.id).first()

        if rank_entry:
            old_score = rank_entry.score
            rank_entry.score = score
            db.commit()
            result = f"🔄 Updated ranking for {name.title()}: old {old_score}, new {score}"
        else:
            new_rank = PokemonRank(name=name, score=score, user_id=user.id)
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

    rank_entry = db.query(PokemonRank).filter_by(name=name, user_id=user.id).first()
    rank = rank_entry.score if rank_entry else None

    return render_template("rankrandom.html", name=name, sprite_url=sprite_url, rank=rank, result=None)


@app.route('/rankings')
def show_all_rankings():
    if 'username' not in session:
        return redirect(url_for('login'))

    db = Session()
    user = db.query(User).filter_by(username=session['username']).first()

    pokemon_list = db.query(Pokemon).order_by(Pokemon.id).all()
    rank_map = {
        r.name: r.score
        for r in db.query(PokemonRank).filter_by(user_id=user.id).all()
    }

    result = [
        {"id": p.id, "name": p.name, "sprite_url": p.sprite_url, "score": rank_map.get(p.name)}
        for p in pokemon_list
    ]

    return render_template("allrankings.html", pokemon_list=result)


@app.route("/update_score", methods=["POST"])
def update_score():
    if 'username' not in session:
        return {"success": False, "error": "User not logged in"}, 403

    db = Session()
    data = request.get_json()
    name = data["name"]
    score = int(data["score"])

    user = db.query(User).filter_by(username=session['username']).first()
    if not user:
        return {"success": False, "error": "User not found"}, 404

    # find or create
    rank_entry = db.query(PokemonRank).filter_by(name=name, user_id=user.id).first()
    if rank_entry:
        rank_entry.score = score
    else:
        rank_entry = PokemonRank(name=name, score=score, user_id=user.id)
        db.add(rank_entry)

    db.commit()
    return {"success": True, "name": name, "score": score}


@app.route('/leaderboard')
def show_leaderboard():
    db = Session()

    # Get only Pokémon that HAVE scores (join + order by)
    ranked = (
        db.query(
            User.username,
            Pokemon.name,
            Pokemon.sprite_url,
            PokemonRank.score
        )
        .join(PokemonRank, User.id == PokemonRank.user_id)
        .join(Pokemon, Pokemon.name == PokemonRank.name)
        .filter(PokemonRank.score.isnot(None))
        .order_by(PokemonRank.score.desc())
        .limit(100)
        .all()
    )

    # Convert to dicts for template
    leaderboard = [
        {
            "username": u,
            "pokemon": n,
            "sprite_url": s,
            "score": sc
        }
        for u, n, s, sc in ranked
    ]

    return render_template("leaderboard.html", leaderboard=leaderboard)



# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

