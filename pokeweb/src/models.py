from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Pokemon(Base):
    __tablename__ = 'pokemon'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    sprite_url = Column(String, nullable=True)   # new column
    data = Column(Text)  # Store raw JSON as a string

class PokemonRank(Base):
    __tablename__ = 'pokemon_rank'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    score = Column(Integer, nullable=False)

# Set up DB connection
engine = create_engine('sqlite:///db.sqlite')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
