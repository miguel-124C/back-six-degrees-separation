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

    def verify_conection_actor(self):
        """
        Controller para ver si hay conexión entre 2 actores.
        """
        idActorA = request.args.get('idActorA', 0)
        idActorB = request.args.get('idActorB', 0)

        try:
            # 1. Obtener datos del servicio
            self.game_service.saved_data_in_db(idActorA, idActorB)

            print('verificacion')
            # 2. Determinar el tipo de respuesta basado en el Accept header
            # Para API: usar el view para formatear la respuesta JSON
            # return self.tmdb_view.format_actors_response(result)
            return jsonify({'message': 'Functionality not yet implemented'}), 200
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500