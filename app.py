import os
import psycopg2
from flask import Flask
from src.controllers.tmdb_controller import TMDBController
from src.controllers.game_controller import GameController

from src.services.tmdb_service import TMDBService
from src.services.actors_service import ActorService
from src.services.movies_service import MovieService
from src.services.actor_movie_service import ActorMovieService
from src.services.game_sevice import GameService

from flask_cors import CORS
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.models.database import Base

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

    conexion_db(app)
    initial_services_controllers(app)

    return app


def initial_services_controllers(app):
    # Iniciar servicios
    tmdb_service = TMDBService(api_key=app.config['TMDB_API_KEY'], base_url=app.config['TMDB_BASE_URL'])
    actor_service = ActorService(app.db)
    movie_service = MovieService(app.db)
    actor_movie_service = ActorMovieService(app.db)
    game_service = GameService(
        actor_service=actor_service,
        movie_service=movie_service,
        actor_movie_service=actor_movie_service,
        tmdb_service=tmdb_service
    )

    # Iniciar controllers
    tmdb_controller = TMDBController(tmdb_service)
    game_controller = GameController(game_service)

    # Registrar blueprints (controllers manejan la API)
    app.register_blueprint(tmdb_controller.blueprint, url_prefix='/tmdb')
    app.register_blueprint(game_controller.blueprint, url_prefix='/game')


def conexion_db(app):
# Configuración de la base de datos
    db_user = os.getenv('DB_USER_NAME', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'movies_db')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')

    try:
        # Crear el engine de SQLAlchemy usando parámetros directamente
        engine = create_engine(
            'postgresql://',
            creator=lambda: psycopg2.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password,
                client_encoding='utf8'
            )
        )
        # Probar la conexión
        with engine.connect() as conn:
            print("Conexión exitosa a la base de datos!")
    except Exception as e:
        print(f"Error al conectar a la base de datos: {str(e)}")
        print(f"Detalles de conexión (sin password):")
        print(f"Host: {db_host}")
        print(f"Port: {db_port}")
        print(f"Database: {db_name}")
        print(f"User: {db_user}")
        raise
    
    # Crear todas las tablas definidas en los modelos
    Base.metadata.create_all(bind=engine)
    
    # Crear la sesión de la base de datos
    db_session = scoped_session(sessionmaker(bind=engine))
    app.db = db_session
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv('PORT', 8000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    app.run(host='0.0.0.0', port=port, debug=debug)