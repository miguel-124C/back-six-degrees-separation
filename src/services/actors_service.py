from src.models.database import Actor
from typing import List
from sqlalchemy.dialects.postgresql import insert

class ActorService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_actor_by_id(self, actor_id):
        actor = self.db_session.query(Actor).filter(Actor.id == actor_id).first()
        # Si no existe, devolver None para que el llamador lo gestione
        if not actor:
            return None

        return {
            'id': actor.id,
            'name': actor.name,
            'profile_path': actor.profile_path,
            'all_movies_saved': actor.all_movies_saved,
            'popularity': actor.popularity
        }

    def create_actor(self, id_person, name, profile_path, popularity):
        new_actor = Actor(name=name, id=id_person, profile_path=profile_path, popularity=popularity)
        self.db_session.add(new_actor)
        self.db_session.commit()
        return new_actor

    def check_movies_saved(self, actor_id, movie_saved: bool):
        # Obtener el objeto ORM directamente (no el dict retornado por get_actor_by_id)
        actor_obj = self.db_session.query(Actor).filter(Actor.id == actor_id).first()
        if not actor_obj:
            return None

        # Actualizar campo en el objeto ORM y persistir
        actor_obj.all_movies_saved = movie_saved
        self.db_session.commit()

        # Devolver la representación en dict como hace get_actor_by_id
        return actor_obj

    def get_actors_by_ids(self, actor_ids: List[int]) -> List[int]:
        """Retorna los IDs de los actores que existen"""
        return [
            actor.id for actor in 
            self.db_session.query(Actor.id)
            .filter(Actor.id.in_(actor_ids))
            .all()
        ]

    def create_actors_bulk(self, actors: List[dict]):
        """
        Crea múltiples actores en una sola transacción.
        IMPORTANTE: Se asume que los actores en la lista ya fueron filtrados
        y no existen en la base de datos.
        """
        if not actors:
            return

        # Usar INSERT ... ON CONFLICT DO NOTHING para ser robusto ante condiciones de carrera
        # Construimos la sentencia con SQLAlchemy core y la ejecutamos en la sesión
        stmt = insert(Actor).values(actors)
        stmt = stmt.on_conflict_do_nothing(index_elements=['id'])

        self.db_session.execute(stmt)
        self.db_session.commit()