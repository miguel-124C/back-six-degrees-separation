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
        movies: List[MovieInterface] = []
        movies = self.__get_list_movies_by_actor__(actor_id)

        for movie in movies:
            exists_movie = self.__add_movie_if_not_exists__(movie['id'], movie['title'], movie['release_date'])
            self.actor_movie_service.add_actor_to_movie(id_actor=actor_id, id_movie=movie['id'], character=movie['character'])
            """ Validacion para que solo se agregue el cast si la pelicula no existia """
            if not exists_movie and not movie['all_cast_saved']:
                self.__add_cast__(movie['id'])
                self.movie_service.check_cast_saved(movie['id'], True)

        self.actor_service.check_movies_saved(actor_id, True)

    def __add_cast__(self, movie_id):
        casts = []
        casts = self.__get_casts_by_movie_id__(movie_id)

        # if not casts:
        #     casts = self.actor_movie_service.get_all_actors_by_movie(movie_id)
        # TODO: Optimizar para que no haga consultas innecesarias
        for cast in casts:
            actor = self.actor_service.get_actor_by_id(cast['id'])

            if not actor:
                self.actor_service.create_actor(id_person=cast['id'], name=cast['name'], profile_path=cast['profile_path'])
            self.actor_movie_service.add_actor_to_movie(id_actor=cast['id'], id_movie=movie_id, character=cast['character'])

    def __add_movie_if_not_exists__(self, movie_id: int, title: str, release_date: str) -> bool:
        """
        Verifica si una peli existe en la base de datos.
        """
        movie = self.movie_service.get_movie_by_id(movie_id)

        if not movie:
            self.movie_service.create_movie(id=movie_id, title=title, release_date=release_date)
            return False
        return True

    def __get_list_movies_by_actor__(self, actor_id: int) -> List[MovieInterface]:
        """
        Obtiene la lista de películas asociadas a un actor dado su ID. TMDB
        """
        movies = self.tmdb_service.get_list_movies_by_actor(actor_id)
        return movies

    def __get_casts_by_movie_id__(self, movie_id: int) -> List[ActorInteface]:
        """
        Obtiene el cast de una película desde TMDB.
        """
        casts = self.tmdb_service.get_movie_credits(movie_id)
        return casts
        
