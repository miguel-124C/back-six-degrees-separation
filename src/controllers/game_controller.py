from flask import Blueprint, request, jsonify
from src.services.tmdb_service import TMDBService
from src.services.game_sevice import GameService

class GameController:
    def __init__(self, game_service: GameService):
        self.game_service = game_service
        self.blueprint = Blueprint('game', __name__)
        self._register_routes()

    def _register_routes(self):
        """Registra todas las rutas del controlador"""
        self.blueprint.add_url_rule(
            '/verify/conection', 'verify_conection', self.verify_conection_actor, methods=['GET']
        )
        self.blueprint.add_url_rule(
            '/verify/connection_with_two_actor', 'verify_shared_conection', self.connection_with_two_actor, methods=['GET']
        )

    def verify_conection_actor(self):
        """
        Controller para ver si hay conexión entre 2 actores.
        """
        idActorA = int(request.args.get('idActorA', 0))
        idActorB = int(request.args.get('idActorB', 0))

        try:
            # 1. Obtener datos del servicio
            self.game_service.saved_data_in_db(idActorA, idActorB)
            ruta = self.game_service.search_connection(idActorA, idActorB)

            if not ruta:
                return jsonify({'connection': False, 'ruta': None}), 200
            else:
                return jsonify({'connection': True, 'ruta': ruta}), 200
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
        
    def connection_with_two_actor(self):
        """
        Controller para ver si 2 actores comparten una peli en comun.
        """
        idActorA = int(request.args.get('idActorA', 0))
        idActorB = int(request.args.get('idActorB', 0))

        if idActorA == idActorB:
            return jsonify({'is_shared':False, 'film': None}), 200

        try:
            # 1. Obtener datos del servicio
            movie_shared = self.game_service.actors_shared_movies(idActorA, idActorB)

            if not movie_shared:
                return jsonify({'is_shared':False, 'film': None}), 200
            else:
                return jsonify({'is_shared':True, 'film': movie_shared}), 200
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500