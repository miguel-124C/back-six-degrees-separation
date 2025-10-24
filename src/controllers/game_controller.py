from flask import Blueprint, request, jsonify
from src.services.tmdb_service import TMDBService

class GameController:
    def __init__(self, tmdb_service: TMDBService):
        self.tmdb_service = tmdb_service
        self.blueprint = Blueprint('game', __name__)
        self._register_routes()

    def _register_routes(self):
        """Registra todas las rutas del controlador"""
        # self.blueprint.add_url_rule(
        #     '/search/actors', 'search_actors', self.search_actors_controller, methods=['GET']
        # )
        pass

    def verify_conection_actor(self):
        """
        Controller para ver si hay conexión entre 2 actores.
        """
        idActorA = request.args.get('idActorA', 0)
        idActorB = request.args.get('idActorB', 0)

        try:
            # 1. Obtener datos del servicio
            # result = self.tmdb_service.search_actors(query)

            # 2. Determinar el tipo de respuesta basado en el Accept header
            # Para API: usar el view para formatear la respuesta JSON
            # return self.tmdb_view.format_actors_response(result)
            pass
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500