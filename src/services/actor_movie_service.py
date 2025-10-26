from src.models.database import ActorMovie, Movie, Actor
from src.interfaces.models_interface import MovieInterface, ActorInteface
from sqlalchemy import and_, tuple_
from typing import List

class ActorMovieService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_actor_movie_by_id(self, actor_movie_id):
        """ Traer una relación actor-película por su ID """
        return self.db_session.query(ActorMovie).filter(ActorMovie.id == actor_movie_id).first()

    def get_all_movies_by_actor(self, actor_id) -> List[MovieInterface]:
        """ Traer todas las películas asociadas a un actor dado su ID """
        # Hacemos un join entre ActorMovie y Movie para obtener los datos de la película
        rows = self.db_session.query(Movie, ActorMovie).join(ActorMovie, ActorMovie.id_movie == Movie.id).filter(ActorMovie.id_actor == actor_id).all()

        if not rows:
            return []

        # Mapear al formato de MovieInterface (creando instancias)
        result: List[MovieInterface] = []
        for movie, actor_movie in rows:
            movie_interface = MovieInterface()
            movie_interface.id = movie.id
            movie_interface.title = movie.title
            movie_interface.release_date = movie.release_date
            movie_interface.character = actor_movie.character
            result.append(movie_interface)

        return result

    def get_all_actors_by_movie(self, movie_id) -> List[ActorInteface]:
        """ Traer todos los actores asociados a una película dado su ID """
        # Hacemos join entre ActorMovie y Actor para devolver datos útiles del actor junto con el personaje
        rows = self.db_session.query(Actor, ActorMovie).join(ActorMovie, ActorMovie.id_actor == Actor.id).filter(ActorMovie.id_movie == movie_id).all()

        if not rows:
            return []

        result = []
        for actor, actor_movie in rows:
            result.append({
                'id': actor.id,
                'name': actor.name,
                'profile_path': actor.profile_path,
                'all_movies_saved': actor_movie.all_movies_saved
            })

        return result

    def add_actor_to_movie(self, id_actor, id_movie, character=None):
        existe = self.db_session.query(ActorMovie).filter(
            and_(
                ActorMovie.id_actor == id_actor,
                ActorMovie.id_movie == id_movie
            )
        ).first()
        
        if existe:
            print(f"El actor ya está en la película {id_movie}")
            return existe  # O None, o lanzar una excepción
        
        # Si no existe, crear nuevo
        nueva_relacion = ActorMovie(
            id_actor=id_actor,
            id_movie=id_movie,
            character=character
        )
        
        self.db_session.add(nueva_relacion)
        self.db_session.commit()
        return nueva_relacion
    
    def add_actor_to_movies_bulk(self, relations: List[dict]):
        """Agrega múltiples relaciones actor-película en una sola transacción"""
        existing = set(
            (r.id_actor, r.id_movie)
            for r in self.db_session.query(ActorMovie.id_actor, ActorMovie.id_movie)
            .filter(
                tuple_(ActorMovie.id_actor, ActorMovie.id_movie).in_(
                    [(r['id_actor'], r['id_movie']) for r in relations]
                )
            )
            .all()
        )
        
        # Filtrar solo las relaciones que no existen
        new_relations = [
            r for r in relations
            if (r['id_actor'], r['id_movie']) not in existing
        ]
        
        if new_relations:
            self.db_session.bulk_insert_mappings(ActorMovie, new_relations)
            self.db_session.commit()