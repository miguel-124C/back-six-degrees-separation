import os
from flask import Flask
from src.controllers.tmdb_controller import tmdb_bp
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

    # Registrar blueprints (controllers manejan la API)
    app.register_blueprint(tmdb_bp, url_prefix='/tmdb')

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    app.run(host='0.0.0.0', port=port, debug=debug)