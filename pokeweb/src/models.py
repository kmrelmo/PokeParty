import os
from sqlalchemy import Column, Integer, String, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class Pokemon(Base):
    __tablename__ = 'pokemon'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    sprite_url = Column(String)
    data = Column(Text)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

class PokemonRank(Base):
    __tablename__ = 'pokemon_rank'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User')

# 🔧 Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db.sqlite")

# ✅ Force the full path inside the container (important for Docker)
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

