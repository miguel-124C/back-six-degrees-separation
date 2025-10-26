from src.models.database import Movie
from src.interfaces.models_interface import MovieInterface
from typing import List

class MovieService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_movie_by_id(self, movie_id) -> MovieInterface:
        movie = self.db_session.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return None

        return {
            'id': movie.id,
            'title': movie.title,
            'release_date': movie.release_date,
            'all_cast_saved': movie.all_cast_saved
        }

    def create_movie(self, id, title, release_date) -> MovieInterface:
        new_movie = Movie(id=id, title=title, release_date=release_date)
        self.db_session.add(new_movie)
        self.db_session.commit()
        return {
            'id': new_movie.id,
            'title': new_movie.title,
            'release_date': new_movie.release_date,
            'all_cast_saved': False
        }
    
    def check_cast_saved(self, movie_id, cast_saved: bool) -> MovieInterface:
        # Obtener el objeto ORM directamente (no el dict retornado por get_actor_by_id)
        movie_obj = self.db_session.query(Movie).filter(Movie.id == movie_id).first()
        if not movie_obj:
            return None

        # Actualizar campo en el objeto ORM y persistir
        movie_obj.all_cast_saved = cast_saved
        self.db_session.commit()

        return movie_obj      
