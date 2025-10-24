import os
from flask import Flask
from src.controllers.tmdb_controller import TMDBController
from src.controllers.game_controller import GameController

from src.services.tmdb_service import TMDBService
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno (local dev). En producción, usa variables del entorno del sistema.
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Configurar CORS con orígenes permitidos desde .env
    origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    CORS(app, resources={r"/*": {"origins": origins}})

    # Configurar desde variables de entorno
    app.config['TMDB_API_KEY'] = os.getenv('TMDB_API_KEY')
    app.config['TMDB_BASE_URL'] = os.getenv('TMDB_BASE_URL')

    # Iniciar servicios
    tmdb_service = TMDBService(api_key=app.config['TMDB_API_KEY'], base_url=app.config['TMDB_BASE_URL'])

    # Iniciar controllers
    tmdb_controller = TMDBController(tmdb_service)
    game_controller = GameController(tmdb_service)

    # Registrar blueprints (controllers manejan la API)
    app.register_blueprint(tmdb_controller.blueprint, url_prefix='/tmdb')
    app.register_blueprint(game_controller.blueprint, url_prefix='/game')

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    app.run(host='0.0.0.0', port=port, debug=debug)