import json, requests
from models import Session, Pokemon

def seed_pokemon_db():
    db = Session()
    for poke_id in range(1, 1026):
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_id}"
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"❌ Failed on ID {poke_id}")
            continue

        data = resp.json()
        name = data["name"]
        sprite_url = data["sprites"]["front_default"]

        # Only insert if not already in DB
        if not db.query(Pokemon).filter_by(id=poke_id).first():
            poke = Pokemon(
                id=poke_id,
                name=name,
                sprite_url=sprite_url,
                data=json.dumps(data)
            )
            db.add(poke)

        if poke_id % 50 == 0:
            db.commit()
            print(f"✅ Seeded {poke_id} Pokémon...")

    db.commit()
    db.close()
    print("🎉 Seeding complete!")
    

if __name__ == "__main__":
    seed_pokemon_db()
