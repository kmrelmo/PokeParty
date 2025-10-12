import json, requests, sys
from models import Session, Pokemon, TypeInfo
from pokemon_data import TYPE_NAMES

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
    

def seed_type_data():
    db = Session()
    def names(arr):
        return [t.get('name') for t in (arr or [])]

    for tname in TYPE_NAMES:
        url = f"https://pokeapi.co/api/v2/type/{tname}"
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"Failed to fetch type {tname}: {resp.status_code}")
            continue
        data = resp.json()
        rel = data.get('damage_relations', {})
        payload = {
            'weak_to': names(rel.get('double_damage_from')),
            'strong_against': names(rel.get('double_damage_to')),
            'resist_from': names(rel.get('half_damage_from')),
            'immune_from': names(rel.get('no_damage_from')),
            'resist_to': names(rel.get('half_damage_to')),
            'immune_to': names(rel.get('no_damage_to')),
        }
        row = db.query(TypeInfo).filter_by(name=tname).first()
        if row:
            row.data = json.dumps(payload)
        else:
            row = TypeInfo(name=tname, data=json.dumps(payload))
            db.add(row)
        db.commit()
        print(f"Seeded type {tname}")
    db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'pokemon':
            seed_pokemon_db()
        elif cmd == 'types':
            seed_type_data()
        else:
            print("Unknown command. Use 'pokemon' or 'types'.")
    else:
        print("Specify what to seed: 'pokemon' or 'types'.")
