from src.models.graphs import Graphs
from src.services.actors_service import ActorService
from src.services.movies_service import MovieService
from src.services.actor_movie_service import ActorMovieService
from src.services.actors_service import ActorService
from src.services.tmdb_service import TMDBService
from src.interfaces.models_interface import ActorInteface, MovieInterface
from typing import List

class GameService:
    def __init__(
            self, actor_service: ActorService, movie_service: MovieService,
            actor_movie_service: ActorMovieService, tmdb_service: TMDBService
        ):
        self.actor_service = actor_service
        self.movie_service = movie_service
        self.actor_movie_service = actor_movie_service
        self.tmdb_service = tmdb_service

    def saved_data_in_db(self, actor_id_a: int, actor_id_b: int) -> bool:
        """
        Guarda en la base de datos la información necesaria para verificar la conexión entre dos actores.
        """
        actorA = self.__add_actor_if_not_exists__(actor_id_a)
        print('Add actor A done')
        if not actorA['all_movies_saved']:
            self.__add_movies_and_cast__(actor_id_a)
            print('Add movies and cast A done')

        actorB = self.__add_actor_if_not_exists__(actor_id_b)
        print('Add actor B done')
        if not actorB['all_movies_saved']:
            self.__add_movies_and_cast__(actor_id_b)
            print('Add movies and cast B done')

        # Lógica para verificar la conexión entre los actores
        # (por ejemplo, buscando películas compartidas)
        # shared_movies = set(movie.id for movie in actor_a.movies).intersection(
        #     set(movie.id for movie in actor_b.movies)
        # )
    
    def __add_actor_if_not_exists__(self, actor_id: int) -> ActorInteface:
        """
        Verifica si un actor existe en la base de datos.
        """
        try:
            actor = self.actor_service.get_actor_by_id(actor_id)

            if not actor:
                actorTMDB = self.tmdb_service.get_actor_details(actor_id) # id, name, profile_path
                self.actor_service.create_actor(id_person=actorTMDB['id'], name=actorTMDB['name'], profile_path=actorTMDB['profile_path'])
                return { 'id': actorTMDB['id'], 'name': actorTMDB['name'], 'profile_path': actorTMDB['profile_path'], 'all_movies_saved': False }
            else:
                return actor
        except Exception as e:
            print( "Error al agregar o verificar actor:", e)

    def __add_movies_and_cast__(self, actor_id: int):
        """
        Agrega películas y su elenco a la base de datos.
        """
         # 1. Obtener todas las películas del actor de una vez
        movies = self.tmdb_service.get_list_movies_by_actor(actor_id)

        # 2. Obtener todos los IDs de películas existentes en un solo query
        existing_movie_ids = set(
            self.movie_service.get_movies_by_ids([m['id'] for m in movies])
        )

        # 3. Preparar lotes para inserción
        movies_to_create = []
        for movie in movies:
            if movie['id'] not in existing_movie_ids:
                movies_to_create.append({
                    'id': movie['id'],
                    'title': movie['title'],
                    'release_date': movie['release_date']
                })
        
        # 4. Crear películas en lote
        if movies_to_create:
            self.movie_service.create_movies_bulk(movies_to_create)

        # 5. Preparar todas las relaciones actor-película
        actor_movie_relations = [
            {'id_actor': actor_id, 'id_movie': movie['id'], 'character': movie['character']}
            for movie in movies
        ]
        
        # 6. Insertar relaciones en lote (ignorando duplicados)
        self.actor_movie_service.add_actor_to_movies_bulk(actor_movie_relations)

        # 7. Procesar el cast de películas nuevas en lote
        movies_needing_cast = [
            m for m in movies 
            if m['id'] not in existing_movie_ids and not m['all_cast_saved']
        ]
        
        if movies_needing_cast:
            self.__add_cast_bulk__([m['id'] for m in movies_needing_cast])
            self.movie_service.check_cast_saved_bulk([m['id'] for m in movies_needing_cast], True)

        # 8. Actualizar estado del actor
        self.actor_service.check_movies_saved(actor_id, True)

    def __add_cast_bulk__(self, movie_ids: List[int]):
        """
        Versión optimizada para agregar el cast de múltiples películas
        """
        # 1. Obtener el cast de todas las películas (mapeado por movie_id)
        all_casts_by_movie = {}
        index = 0
        for movie_id in movie_ids:
            index += 1
            print(index)
            casts = self.tmdb_service.get_movie_credits(movie_id)
            all_casts_by_movie[movie_id] = casts

        # 2. Extraer IDs únicos de actores
        unique_actor_ids = {cast['id'] for casts in all_casts_by_movie.values() for cast in casts}

        # 3. Obtener actores existentes en un solo query
        existing_actor_ids = set(self.actor_service.get_actors_by_ids(list(unique_actor_ids)))

        # 4. Preparar actores nuevos para inserción en lote (una sola entrada por actor)
        actors_map = {}
        for casts in all_casts_by_movie.values():
            for cast in casts:
                # guardar la primera aparición del actor
                if cast['id'] not in actors_map:
                    actors_map[cast['id']] = cast

        actors_to_create = [
            {
                'id': aid,
                'name': actors_map[aid]['name'],
                'profile_path': actors_map[aid].get('profile_path')
            }
            for aid in actors_map.keys()
            if aid not in existing_actor_ids
        ]
        print(f"Creating {len(actors_to_create)} new actors")

        # 5. Crear actores en lote (lista ya deduplicada por id)
        if actors_to_create:
            self.actor_service.create_actors_bulk(actors_to_create)

        # 6. Preparar todas las relaciones actor-película (solo las reales por película)
        relations = []
        for movie_id, casts in all_casts_by_movie.items():
            for cast in casts:
                relations.append({
                    'id_actor': cast['id'],
                    'id_movie': movie_id,
                    'character': cast.get('character')
                })

        # 7. Insertar relaciones en lote
        if relations:
            self.actor_movie_service.add_actor_to_movies_bulk(relations)

    def __add_movie_if_not_exists__(self, movie_id: int, title: str, release_date: str) -> bool:
        """
        Verifica si una peli existe en la base de datos.
        """
        movie = self.movie_service.get_movie_by_id(movie_id)

        if not movie:
            self.movie_service.create_movie(id=movie_id, title=title, release_date=release_date)
            return False
        return True
        
