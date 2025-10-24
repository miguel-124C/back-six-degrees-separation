from flask import current_app
import httpx


def search_actors(query: str):
    """
    Busca actores usando la API de TMDB.
    """

    api_key = current_app.config.get('TMDB_API_KEY')
    base_url = current_app.config.get('TMDB_BASE_URL')

    if not query:
        return {'error': 'Query parameter "q" is required.'}, 400

    params = {
        'query': query,
        'include_adult': 'false',
        'language': 'en-US',
        'page': 1
    }

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{base_url}/search/person",
                params=params,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        actors = []
        for person in data.get('results', []):
            if person.get('known_for_department') == "Acting":
                profile_path = person.get('profile_path')
                if profile_path:
                    profile_path = f"https://image.tmdb.org/t/p/original{profile_path}"
                actors.append({
                    'id': person.get('id'),
                    'name': person.get('name'),
                    'profile_path': profile_path,
                    'popularity': person.get('popularity')
                })

        actors.sort(key=lambda x: x.get('popularity', 0), reverse=True)
        return actors
    except Exception as e:
        return {'error': str(e)}, 500
