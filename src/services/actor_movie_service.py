from src.models.database import ActorMovie, Movie, Actor
from src.interfaces.models_interface import MovieInterface, ActorInteface
from sqlalchemy import and_, tuple_, func, distinct
from typing import List

from sqlalchemy import select

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

    def shared_movies(self, actor_a: int, actor_b: int) -> bool:
        # Traer todas las peliculas en donde 2 actores compartieron pantalla
        stmt = select(
            Movie.id,
            Movie.title,
            Movie.release_date,
            Movie.vote_average,
            Movie.poster_path
        ).join(ActorMovie, ActorMovie.id_movie == Movie.id)\
         .join(Actor, Actor.id == ActorMovie.id_actor)\
         .where(
            Actor.id.in_((actor_a, actor_b))
         ).group_by(
             Movie.id, Movie.title, Movie.release_date
         ).having(
            func.count(distinct(Actor.id)) > 1
         ).order_by( Movie.vote_average.desc() )
        
        movies = self.db_session.execute(stmt).mappings().all()
        return movies

    def get_all_actors_asociated_with_one(self, id_actor: int) -> list:
        """ Traer la conexión más reciente para cada co-protagonista único. """
        
        # 1. CTE/Subconsulta para encontrar y numerar las películas compartidas
        movie_ids_query = select(ActorMovie.id_movie).where(ActorMovie.id_actor == id_actor)

        subquery = select(
            Actor.id.label('id_co_actor'),
            Movie.id.label('movie_id'),
            Movie.title,
            Movie.poster_path,
            # Numera las películas de cada actor, ordenando por fecha descendente.
            # La más reciente obtiene el número 1.
            func.row_number().over(
                partition_by=Actor.id,
                order_by=Movie.release_date.desc()
            ).label('row_num')
        ).join(ActorMovie, ActorMovie.id_movie == Movie.id)\
        .join(Actor, Actor.id == ActorMovie.id_actor)\
        .where(
            Movie.id.in_(movie_ids_query),
            Actor.id != id_actor,
            ActorMovie.order <= 50
        ).subquery('ranked_movies')

        # 2. Consulta final para seleccionar solo la fila número 1 de cada actor
        stmt = select(
            subquery.c.id_co_actor,
            subquery.c.movie_id,
            subquery.c.title,
            subquery.c.poster_path,
        ).where(subquery.c.row_num == 1)

        # 3. Ejecutar y formatear
        results_list_of_dicts = self.db_session.execute(stmt).mappings().all()

        edges_for_graph = []
        for row in results_list_of_dicts:
            attr = {'movie_id': row['movie_id'], 'movie_title': row['title'], 'poster_path': row['poster_path']}
            edge = (id_actor, row['id_co_actor'], attr)
            edges_for_graph.append(edge)

        return edges_for_graph