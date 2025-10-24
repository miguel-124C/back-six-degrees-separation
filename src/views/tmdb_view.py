from flask import jsonify

def format_actors_response(result):
    """
    Vista que formatea la respuesta de actores para la API.
    Solo se encarga de la presentación de datos, no de la lógica de negocio.
    """
    return jsonify(result)

def api_status():
    """Endpoint informativo que muestra el estado de la API."""
    return jsonify({
        'message': 'TMDB API is running',
        'status': 'ok',
        'version': '1.0'
    })