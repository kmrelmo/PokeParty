from models import Session, Pokemon
db = Session()
print(db.query(Pokemon).count())