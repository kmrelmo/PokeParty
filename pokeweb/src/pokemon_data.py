# utils.py
import json
from models import Session, Pokemon, PokemonRank
import requests
import random

def extract_sprite(pokemon_data):
    return pokemon_data['sprites']['front_default']

def extract_sprites(data):
    sprites = []

    def find_images(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                find_images(v)
        elif isinstance(obj, str) and obj.startswith("http"):
            sprites.append(obj)

    find_images(data["sprites"])
    return sprites

def extract_types(pokemon_data):
    return [t['type']['name'] for t in pokemon_data['types']]

def extract_stats(pokemon_data):
    return {stat['stat']['name']: stat['base_stat'] for stat in pokemon_data['stats']}

def extract_moves(pokemon_data, count=5):
    return [m['move']['name'] for m in pokemon_data['moves'][:count]]

def get_random_pokemon_id(max_id=1025):
    """Return a random Pokémon ID up to max_id."""
    return random.randint(1, max_id)

def fetch_pokemon(name_or_id):
    """Fetch Pokémon data from API (by name or ID). Returns JSON or None."""
    url = f'https://pokeapi.co/api/v2/pokemon/{name_or_id}'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def fetch_species(url):
    """Fetch Pokémon species data from a given URL. Returns JSON or {}."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return {}

def get_or_cache_pokemon(name):
    """Return Pokémon data from DB if cached, otherwise fetch + store it."""
    db = Session()
    name = name.lower()
    poke = db.query(Pokemon).filter_by(name=name).first()

    if poke:
        return json.loads(poke.data)

    data = fetch_pokemon(name)
    if not data:
        return None

    new_poke = Pokemon(id=data['id'], name=name, data=json.dumps(data))
    db.add(new_poke)
    db.commit()
    return data

def build_clues(data, species):
    """Construct a list of clues for statsguess game."""
    stats = extract_stats(data)
    height = data["height"]
    weight = data["weight"]
    types = [t['type']['name'] for t in data['types']]
    generation = species.get("generation", {}).get("name")
    desc = None
    for entry in species.get("flavor_text_entries", []):
        if entry["language"]["name"] == "en":
            desc = entry["flavor_text"]
            break

    return [
        {"type": "stats", "value": stats},
        {"type": "height", "value": height},
        {"type": "weight", "value": weight},
        {"type": "types", "value": types},
        {"type": "generation", "value": generation},
        {"type": "desc", "value": desc}
    ]

def check_db_for_ranking(name):
    db = Session()
    rank_entry = db.query(PokemonRank).filter_by(name=name).first()
    if rank_entry:
        return True, rank_entry.score
    return False, None

def update_ranking(name, score):
    db = Session()
    rank_entry = db.query(PokemonRank).filter_by(name=name).first()
    if rank_entry:
        old_score = rank_entry.score
        rank_entry.score = score
        db.commit()
        return old_score, score
    else:
        new_rank = PokemonRank(name=name, score=score)
        db.add(new_rank)
        db.commit()
        return None, score
