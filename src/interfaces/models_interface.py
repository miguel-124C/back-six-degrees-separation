

# Interface for actor

class ActorInteface:
    def __init__(self):
        self.id: int
        self.name: str
        self.profile_path: str
        self.character: str
        self.all_movies_saved: bool = False
        pass

class MovieInterface:
    def __init__(self):
        self.id: int
        self.title: str
        self.release_date: str
        self.character: str
        self.all_cast_saved: bool = False
        pass