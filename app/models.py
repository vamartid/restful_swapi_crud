from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

# Association tables
character_film = Table(
    "character_film",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("character.id")),
    Column("film_id", Integer, ForeignKey("film.id")),
)

character_starship = Table(
    "character_starship",
    Base.metadata,
    Column("character_id", Integer, ForeignKey("character.id")),
    Column("starship_id", Integer, ForeignKey("starship.id")),
)

film_starship = Table(
    "film_starship",
    Base.metadata,
    Column("film_id", Integer, ForeignKey("film.id")),
    Column("starship_id", Integer, ForeignKey("starship.id")),
)

# Models
class Character(Base):
    __tablename__ = "character"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    gender = Column(String(20))
    birth_year = Column(String(20))
    films = relationship("Film", secondary=character_film, back_populates="characters")
    starships = relationship("Starship", secondary=character_starship, back_populates="characters")


class Film(Base):
    __tablename__ = "film"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), unique=True, nullable=False)
    director = Column(String(100))
    release_date = Column(String(20))
    characters = relationship("Character", secondary=character_film, back_populates="films")
    starships = relationship("Starship", secondary=film_starship, back_populates="films")


class Starship(Base):
    __tablename__ = "starship"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    model = Column(String(100))
    manufacturer = Column(String(100))
    characters = relationship("Character", secondary=character_starship, back_populates="starships")
    films = relationship("Film", secondary=film_starship, back_populates="starships")
