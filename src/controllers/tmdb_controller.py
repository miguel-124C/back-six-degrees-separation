from flask import Blueprint, request, jsonify
from src.services.tmdb_service import search_actors
from src.views.tmdb_view import format_actors_response

tmdb_bp = Blueprint('tmdb', __name__)

@tmdb_bp.route('/search/actors', methods=['GET'])
def search_actors_controller():
    """
    Controller para la búsqueda de actores.
    Maneja la lógica de la petición y coordina el servicio y la vista.
    """
    query = request.args.get('q', '')

    try:
        # 1. Obtener datos del servicio
        result = search_actors(query)

        # 2. Determinar el tipo de respuesta basado en el Accept header
        # Para API: usar el view para formatear la respuesta JSON
        return format_actors_response(result)
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500