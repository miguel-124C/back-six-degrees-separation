

# Interface of models of DB

class ActorInteface:
    def __init__(self):
        self.id: int
        self.name: str
        self.profile_path: str
        self.popularity: float
        self.character: str
        self.all_movies_saved: bool = False
        pass

class MovieInterface:
    def __init__(self):
        self.id: int
        self.title: str
        self.release_date: str
        self.poster_path: str
        self.vote_average: float
        self.character: str
        self.all_cast_saved: bool = False
        pass