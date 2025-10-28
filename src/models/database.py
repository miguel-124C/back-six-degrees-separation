from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, DateTime, Boolean, func, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index

Base = declarative_base()

class Actor(Base):
    __tablename__ = 'actors'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    profile_path = Column(String(255))
    popularity = Column(Float(), server_default='0.0')
    last_updated = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    all_movies_saved = Column(Boolean, nullable=False, server_default='0')

    __table_args__ = (
        # Índices para consultas frecuentes
        Index('idx_actors_name', 'name'),  # Para búsquedas por nombre
        Index('idx_actors_popularity', 'popularity'),  # Para ordenar por popularidad
        Index('idx_actors_all_movies', 'all_movies_saved'),  # Para filtrar por estado
    )

class Movie(Base):
    __tablename__ = 'movies'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(500), nullable=False)
    release_date = Column(String(15))
    poster_path = Column(String(255))
    vote_average = Column(Float(), server_default='0.0')
    all_cast_saved = Column(Boolean, nullable=False, server_default='0')

    __table_args__ = (
        # Índices para consultas frecuentes
        Index('idx_movies_release_date', 'release_date'),
        Index('idx_movies_vote_avg', 'vote_average'),
        Index('idx_movies_title', 'title'),  # Para búsquedas por título
        Index('idx_movies_all_cast', 'all_cast_saved'),  # Para filtrar por estado
    )

class ActorMovie(Base):
    __tablename__ = 'actors_movies'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    id_actor = Column(BigInteger, ForeignKey('actors.id'), nullable=False, index=True)
    id_movie = Column(BigInteger, ForeignKey('movies.id'), nullable=False, index=True)
    character = Column(String(500), nullable=False, server_default='None')
    order = Column(Integer, server_default='0')

    # Enforce a unique constraint at the DB level so the same (actor, movie)
    # pair cannot be inserted twice.
    __table_args__ = (
        UniqueConstraint('id_actor', 'id_movie', name='uix_actor_movie'),
        # Índices adicionales para optimizar consultas
        Index('idx_actor_movie_actor', 'id_actor'),
        Index('idx_actor_movie_movie', 'id_movie'),
        Index('idx_actor_movie_order', 'id_movie', 'order'),  # Útil para ordenar el reparto
    )