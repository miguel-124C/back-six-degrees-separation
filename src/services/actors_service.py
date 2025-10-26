from src.models.database import Actor

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
            'all_movies_saved': actor.all_movies_saved
        }

    def create_actor(self, name, id_person, profile_path):
        new_actor = Actor(name=name, id=id_person, profile_path=profile_path)
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

    # def delete_actor(self, actor_id):
    #     actor = self.get_actor_by_id(actor_id)
    #     if actor:
    #         self.db_session.delete(actor)
    #         self.db_session.commit()
    #         return True
    #     return False