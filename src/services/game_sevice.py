from src.models.graphs import Graphs
from src.services.actors_service import ActorService
from src.services.movies_service import MovieService
from src.services.actor_movie_service import ActorMovieService
from src.services.tmdb_service import TMDBService
from src.interfaces.models_interface import ActorInteface
from typing import List
import time
import concurrent.futures
from typing import Dict, Any

class GameService:
    def __init__(
            self, actor_service: ActorService, movie_service: MovieService,
            actor_movie_service: ActorMovieService, tmdb_service: TMDBService
        ):
        self.actor_service = actor_service
        self.movie_service = movie_service
        self.actor_movie_service = actor_movie_service
        self.tmdb_service = tmdb_service
        # Tunable parameters to avoid overloading the TMDB API / reduce bursts
        # You can lower max_workers and increase rate_limit_pause if you still hit limits.
        self._max_workers = 6
        self._chunk_size = 20
        self._max_retries = 3
        self._rate_limit_pause = 0.25  # seconds pause between chunks
        self.graphs = Graphs(self.actor_movie_service)

    def saved_data_in_db(self, actor_id_a: int, actor_id_b: int) -> bool:
        """
        Guarda en la base de datos la información necesaria para verificar la conexión entre dos actores.
        """
        actorA = self.__add_actor_if_not_exists__(actor_id_a)
        if actorA and not actorA['all_movies_saved']:
            print('Add actor A done')
            self.__add_movies_and_cast__(actor_id_a)
            print('Add movies and cast A done')

        actorB = self.__add_actor_if_not_exists__(actor_id_b)
        if actorB and not actorB['all_movies_saved']:
            print('Add actor B done')
            self.__add_movies_and_cast__(actor_id_b)
            print('Add movies and cast B done')
    
    def __add_actor_if_not_exists__(self, actor_id: int) -> ActorInteface:
        """
        Verifica si un actor existe en la base de datos.
        """
        try:
            actor = self.actor_service.get_actor_by_id(actor_id)

            if not actor:
                actorTMDB = self.tmdb_service.get_actor_details(actor_id) # id, name, profile_path, popularity
                if not actorTMDB:
                    return None
                self.actor_service.create_actor(
                    id_person=actorTMDB['id'], name=actorTMDB['name'],
                    profile_path=actorTMDB['profile_path'], popularity=actorTMDB['popularity']
                )
                return actorTMDB
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
                    'release_date': movie['release_date'],
                    'poster_path': movie['poster_path'],
                    'vote_average': movie['vote_average']
                })
        
        # 4. Crear películas en lote
        if movies_to_create:
            self.movie_service.create_movies_bulk(movies_to_create)

        # 5. Preparar todas las relaciones actor-película
        actor_movie_relations = [
            {'id_actor': actor_id, 'id_movie': movie['id'], 'character': movie['character'], 'order': movie.get('order', 0)}
            for movie in movies
        ]

        # Evitar duplicados dentro del mismo lote (mismo actor en la misma película
        # puede aparecer varias veces por datos repetidos)
        deduped_relations = []
        seen_pairs = set()
        for r in actor_movie_relations:
            pair = (r['id_actor'], r['id_movie'])
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            deduped_relations.append(r)

        # Filtrar relaciones que ya existen en la BD para este actor (reduce trabajo
        # en add_actor_to_movies_bulk y evita duplicados si la relación ya estaba)
        try:
            existing_movies_for_actor = set(m.id for m in self.actor_movie_service.get_all_movies_by_actor(actor_id))
        except Exception as e:
            print(f"Error comprobando películas existentes para actor {actor_id}: {e}")
            existing_movies_for_actor = set()

        relations_to_insert = [r for r in deduped_relations if r['id_movie'] not in existing_movies_for_actor]

        # 6. Insertar relaciones en lote (el servicio a su vez filtra lo que ya está en BD)
        if relations_to_insert:
            try:
                self.actor_movie_service.add_actor_to_movies_bulk(relations_to_insert)
            except Exception as e:
                print(f"Error adding actor-movie relations in bulk: {e}")

        # 7. Procesar el cast de películas nuevas en lote
        movies_needing_cast = [
            m for m in movies
            if m['id'] not in existing_movie_ids
        ]
        
        print(f"Movies needing cast: {len(movies_needing_cast)}")
        if movies_needing_cast:
            self.__add_cast_bulk__([m['id'] for m in movies_needing_cast])
            self.movie_service.check_cast_saved_bulk([m['id'] for m in movies_needing_cast], True)

        # 8. Actualizar estado del actor
        self.actor_service.check_movies_saved(actor_id, True)

    def __add_cast_bulk__(self, movie_ids: List[int]):
        """
        Versión optimizada para agregar el cast de múltiples películas
        """
        # Strategy:
        # - Fetch credits concurrently but bound concurrency with ThreadPoolExecutor
        # - Process movie_ids in chunks to avoid bursting the API
        # - Retry individual movie credit fetches with exponential backoff
        # - Continue on failures (log and skip) so a single failure doesn't stop the whole batch

        all_casts_by_movie: Dict[int, List[Dict[str, Any]]] = {}

        def fetch_with_retries(mid: int):
            attempt = 0
            while attempt < self._max_retries:
                try:
                    # Call the TMDB service; let it raise on network errors so we can retry here
                    casts = self.tmdb_service.get_movie_credits(mid)
                    # Normalize None -> empty list
                    if casts is None:
                        casts = []
                    return mid, casts
                except Exception as e:
                    attempt += 1
                    backoff = 0.5 * (2 ** (attempt - 1))
                    print(f"Error fetching credits for {mid} (attempt {attempt}/{self._max_retries}): {e}. Backing off {backoff}s")
                    time.sleep(backoff)
            # All retries failed
            print(f"Failed to fetch credits for movie {mid} after {self._max_retries} attempts. Skipping.")
            return mid, []

        # Process in chunks to limit burst rate and optionally sleep between chunks
        for i in range(0, len(movie_ids), self._chunk_size):
            chunk = movie_ids[i:i + self._chunk_size]
            with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                future_to_mid = {executor.submit(fetch_with_retries, mid): mid for mid in chunk}
                for fut in concurrent.futures.as_completed(future_to_mid):
                    mid = future_to_mid[fut]
                    try:
                        movie_id, casts = fut.result()
                        all_casts_by_movie[movie_id] = casts
                    except Exception as e:
                        # Shouldn't happen because fetch_with_retries catches, but just in case
                        print(f"Unexpected error fetching {mid}: {e}")
            # small pause between chunks to reduce burst risk
            time.sleep(self._rate_limit_pause)

        # 2. Extraer IDs únicos de actores
        unique_actor_ids = {cast['id'] for casts in all_casts_by_movie.values() for cast in casts}

        # 3. Obtener actores existentes en un solo query
        if unique_actor_ids:
            existing_actor_ids = set(self.actor_service.get_actors_by_ids(list(unique_actor_ids)))
        else:
            existing_actor_ids = set()

        # 4. Preparar actores nuevos para inserción en lote (una sola entrada por actor)
        actors_map: Dict[int, Dict[str, Any]] = {}
        for casts in all_casts_by_movie.values():
            for cast in casts:
                if cast and 'id' in cast and cast['id'] not in actors_map:
                    actors_map[cast['id']] = cast

        actors_to_create = [
            {
                'id': aid,
                'name': actors_map[aid].get('name'),
                'profile_path': actors_map[aid].get('profile_path'),
                'popularity': actors_map[aid].get('popularity', 0.0)
            }
            for aid in actors_map.keys()
            if aid not in existing_actor_ids
        ]
        print(f"Creating {len(actors_to_create)} new actors")

        # 5. Crear actores en lote (lista ya deduplicada por id)
        if actors_to_create:
            try:
                self.actor_service.create_actors_bulk(actors_to_create)
            except Exception as e:
                print(f"Error creating actors bulk: {e}")

        # 6. Preparar todas las relaciones actor-película (solo las reales por película)
        relations = []
        for movie_id, casts in all_casts_by_movie.items():
            for cast in casts:
                if not cast or 'id' not in cast:
                    continue
                relations.append({
                    'id_actor': cast['id'],
                    'id_movie': movie_id,
                    'character': cast.get('character'),
                    'order': cast.get('order', 0)
                })

        # Evitar duplicados dentro del mismo lote (mismo actor en la misma película
        # puede aparecer varias veces en distintos casts o por datos repetidos)
        deduped_relations = []
        seen_pairs = set()
        for r in relations:
            pair = (r['id_actor'], r['id_movie'])
            if pair in seen_pairs:
                # saltar duplicados internos
                continue
            seen_pairs.add(pair)
            deduped_relations.append(r)

        # 7. Insertar relaciones en lote (el servicio ya filtra las que están en la BD,
        # aquí prevenimos inserciones múltiples dentro del mismo batch)
        if deduped_relations:
            try:
                self.actor_movie_service.add_actor_to_movies_bulk(deduped_relations)
            except Exception as e:
                print(f"Error adding actor-movie relations in bulk: {e}")

    def search_connection(self, actor_a_id: int, actor_b_id: int):
        """
        Se busca todos los actores asociados a uno
        Luego se agrega esos al grafo para luego buscar mediandte el algoritmo BFS
        """
        # Antes se tenia asi, se creaba cada vez el objeto, hacia lento las operaciones, ya que no se persistian los nodos y aristas
        # graphs = Graphs(self.actor_movie_service)

        # BSF unidireccional
        # ruta = self.graphs.bfs(actor_a_id, actor_b_id)
        ruta = self.graphs.bfs_bidireccional(actor_a_id, actor_b_id)
        if not ruta:
            return None
        
        ruta_con_actores: List = []
        for r in ruta:
            actor1 = self.actor_service.get_actor_by_id(r[0])
            actor2 = self.actor_service.get_actor_by_id(r[2])
            ruta_con_actores.append({
                'actual': actor1,
                'movie': r[1],
                'destino': actor2
            })
        return ruta_con_actores

    def actors_shared_movies(self, actora_id: int, actorb_id):
        actorA = self.__add_actor_if_not_exists__(actora_id)
        if actorA and not actorA['all_movies_saved']:
            print('Add actor A done')
            self.__add_movies_and_cast__(actora_id)
            print('Add movies and cast A done')

        actorB = self.__add_actor_if_not_exists__(actorb_id)
        if actorB and not actorB['all_movies_saved']:
            print('Add actor B done')
            self.__add_movies_and_cast__(actorb_id)
            print('Add movies and cast B done')
        movies_shared = self.actor_movie_service.shared_movies(actora_id, actorb_id)

        if not movies_shared:
            return None
        
        first_movie = movies_shared[0]
        movie_shared_populate = {
            'id': first_movie.id,
            'title': first_movie.title,
            'release_date': first_movie.release_date,
            'vote_average': first_movie.vote_average,
            'poster_path': first_movie.poster_path
        }
        return movie_shared_populate