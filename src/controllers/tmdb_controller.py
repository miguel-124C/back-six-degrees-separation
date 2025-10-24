from flask import Blueprint, request, jsonify
from src.views.tmdb_view import TMDBView
from src.services.tmdb_service import TMDBService

class TMDBController:
    def __init__(self, tmdb_service: TMDBService):
        self.tmdb_service = tmdb_service
        self.tmdb_view = TMDBView
        self.blueprint = Blueprint('tmdb', __name__)
        self._register_routes()

    def _register_routes(self):
        """Registra todas las rutas del controlador"""
        self.blueprint.add_url_rule(
            '/search/actors', 'search_actors', self.search_actors_controller, methods=['GET']
        )
        self.blueprint.add_url_rule(
            '/all/movies', 'list_movies', self.list_movies_by_actor, methods=['GET']
        )
        self.blueprint.add_url_rule(
            '/movie/cast/<int:movie_id>', 'cast_movie', self.get_movie_cast, methods=['GET']
        )

    def search_actors_controller(self):
        """
        Controller para la búsqueda de actores.
        Maneja la lógica de la petición y coordina el servicio y la vista.
        """
        query = request.args.get('q', '')

        try:
            # 1. Obtener datos del servicio
            result = self.tmdb_service.search_actors(query)

            # 2. Determinar el tipo de respuesta basado en el Accept header
            # Para API: usar el view para formatear la respuesta JSON
            return self.tmdb_view.format_actors_response(result)
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

    def list_movies_by_actor(self, actor_id):
        """
        Controller para la búsqueda de actores.
        Maneja la lógica de la petición y coordina el servicio y la vista.
        """

        try:
            # 1. Obtener datos del servicio
            result = self.tmdb_service.get_list_movies_by_actor(actor_id)

            # 2. Determinar el tipo de respuesta basado en el Accept header
            # Para API: usar el view para formatear la respuesta JSON
            return self.tmdb_view.format_actors_response(result)
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    
    def get_movie_cast(self, movie_id):
        """
        Controller para obtener el cast de una película.
        """

        try:
            # 1. Obtener datos del servicio
            result = self.tmdb_service.get_movie_credits(movie_id)

            # 2. Determinar el tipo de respuesta basado en el Accept header
            # Para API: usar el view para formatear la respuesta JSON
            return self.tmdb_view.format_actors_response(result)
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500