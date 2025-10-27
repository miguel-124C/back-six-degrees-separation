from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Boolean, func, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Actor(Base):
    __tablename__ = 'actors'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    profile_path = Column(String(255))
    popularity = Column(Float(), server_default='0.0')
    last_updated = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    all_movies_saved = Column(Boolean, nullable=False, server_default='0')

    # Relación con movies a través de actors_movies
    movies = relationship('Movie', secondary='actors_movies', back_populates='actors')

class Movie(Base):
    __tablename__ = 'movies'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(500), nullable=False)
    release_date = Column(String(15))
    poster_path = Column(String(255))
    vote_average = Column(Float(), server_default='0.0')
    all_cast_saved = Column(Boolean, nullable=False, server_default='0')

    # Relación con actors a través de actors_movies
    actors = relationship('Actor', secondary='actors_movies', back_populates='movies')

class ActorMovie(Base):
    __tablename__ = 'actors_movies'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    id_actor = Column(BigInteger, ForeignKey('actors.id'), nullable=False)
    id_movie = Column(BigInteger, ForeignKey('movies.id'), nullable=False)
    character = Column(String(500), nullable=False, server_default='None')
    order = Column(Integer, server_default='0')

    # Enforce a unique constraint at the DB level so the same (actor, movie)
    # pair cannot be inserted twice.
    __table_args__ = (
        UniqueConstraint('id_actor', 'id_movie', name='uix_actor_movie'),
    )