import httpx

class TMDBService:

    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url

        # Manejando variables para evitar duplicación
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.url_images = "https://image.tmdb.org/t/p/original"

    def search_actors(self, query: str):
        """
        Busca actores usando la API de TMDB.
        """
        if not query:
            return {'error': 'Query parameter "q" is required.'}, 400

        params = {
            'query': query,
            'include_adult': 'false',
            'language': 'en-US',
            'page': 1
        }

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/search/person",
                    params=params,
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

            actors = []
            for person in data.get('results', []):
                if person.get('known_for_department') == "Acting":
                    actors.append({
                        'id': person.get('id'),
                        'name': person.get('name'),
                        'profile_path': person.get('profile_path'),
                        'popularity': person.get('popularity')
                    })

            actors.sort(key=lambda x: x.get('popularity', 0), reverse=True)
            return actors
        except Exception as e:
            return {'error': str(e)}, 500
        
    def get_list_movies_by_actor(self, actor_id: int):
        """
        Obtiene la lista de películas asociadas a un actor dado su ID.
        """

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/person/{actor_id}/movie_credits",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

            movies = []
            for movie in data.get('cast', []):
                movies.append({
                    'id': movie.get('id'),
                    'title': movie.get('title'),
                    'poster_path': movie.get('poster_path'),
                    'release_date': movie.get('release_date'),
                    'vote_average': movie.get('vote_average'),
                    'character': movie.get('character'),
                    'order': movie.get('order')
                })

            movies = sorted(movies, key=lambda x: x.get('release_date', ''), reverse=True)[:150]
            return movies
        except Exception as e:
            return {'error': str(e)}, 500
        
    def get_movie_credits(self, movie_id: int):
        """
        Obtiene los créditos de una película dada su ID.
        """

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/movie/{movie_id}/credits",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

            cast = []
            for person in data.get('cast', []):
                cast.append({
                    'id': person.get('id'),
                    'name': person.get('name'),
                    'profile_path': person.get('profile_path'),
                    'popularity': person.get('popularity'),
                    'character': person.get('character'),
                    'order': person.get('order')
                })

            cast = sorted(cast, key=lambda x: x.get('order', ''))[:80]
            print("CAST TMDB:", len(cast))
            return cast
        except Exception as e:
            return {'error': str(e)}, 500
        
    def get_actor_details(self, actor_id: int):
        """
        Obtiene los detalles de un actor dado su ID.
        """

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/person/{actor_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

            actor_details = {
                'id': data.get('id'),
                'name': data.get('name'),
                'profile_path': data.get('profile_path'),
                'popularity': data.get('popularity')
            }

            return {
                'id': actor_details['id'], 'name': actor_details['name'],
                'profile_path': actor_details['profile_path'], 'popularity': actor_details['popularity'],
                'all_movies_saved': False
            }
        except Exception as e:
            return {'error': str(e)}, 500
        
    def get_movie_details(self, movie_id: int):
        """
        Obtiene los detalles de una película dada su ID.
        """

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/movie/{movie_id}",
                    headers=self.headers
                )
                response.raise_for_status()
                data = response.json()

            movie_details = {
                'id': data.get('id'),
                'title': data.get('title'),
                'poster_path': data.get('poster_path'),
                'release_date': data.get('release_date')
            }

            return movie_details
        except Exception as e:
            return {'error': str(e)}, 500
