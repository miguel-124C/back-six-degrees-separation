from collections import deque, defaultdict
from src.services.actor_movie_service import ActorMovieService

class Graphs:
    """
    Representación de un Grafo No Dirigido usando Lista de Adyacencia.
    """
    def __init__(self, actor_movie_service: ActorMovieService):
        # El diccionario almacena la lista de adyacencia.
        # {vertice: [vecino1, vecino2, ...]}
        # defaultdict facilita agregar nuevos vértices sin inicialización manual.
        self.lista_adyacencia = defaultdict(list)
        self.num_vertices = 0
        self.service = actor_movie_service # Referencia al servicio DB
        self.loaded_vertices = set() # Conjunto para rastrear qué IDs ya tienen sus vecinos cargados
        
    def agregar_vertice(self, vertice):
        """Agrega un vértice si no existe. (Nodo) id"""
        if vertice not in self.lista_adyacencia:
            self.lista_adyacencia[vertice] = []
            self.num_vertices += 1

    def agregar_arista(self, u, v, attr):
        """
        Agrega una arista entre u y v.
        Asume un grafo NO DIRIGIDO, por lo que agrega la conexión en ambas direcciones.
        """
        # Asegura que ambos vértices existan en el grafo
        self.agregar_vertice(u)
        self.agregar_vertice(v)

        # 3. Agrega la arista en la dirección u -> v
        # Se verifica si ya existe una arista a 'v' para evitar duplicados.
        # Solo verificamos el ID del vecino, no los atributos, para la unicidad.
        if not any(vecino_id == v for vecino_id, _ in self.lista_adyacencia[u]):
            self.lista_adyacencia[u].append((v, attr))
        
        # 4. Define y agrega la arista en la dirección v -> u (Grafo NO DIRIGIDO)
        if not any(vecino_id == u for vecino_id, _ in self.lista_adyacencia[v]):
            self.lista_adyacencia[v].append((u, attr))

    def obtener_vecinos(self, vertice):
        """Retorna la lista de vecinos de un vértice."""
        return self.lista_adyacencia.get(vertice, [])
    
    def __str__(self):
        """Representación legible del grafo."""
        output = "Grafo ({} Vértices):\n".format(self.num_vertices)
        for u, vecinos in self.lista_adyacencia.items():
            output += f"  {u}: {vecinos}\n"
        return output

    def expandir_vertice(self, u):
        """Carga los vecinos de 'u' desde la DB si aún no se han cargado."""
        if u not in self.loaded_vertices:
            # 1. Obtener las aristas (u, v, attr) desde la DB
            edges = self.service.get_all_actors_asociated_with_one(u)
            
            # 2. Agregar las aristas al grafo
            for origen, destino, attr in edges:
                self.agregar_arista(origen, destino, attr)
            
            # 3. Marcar el vértice como cargado para no consultarlo de nuevo.
            self.loaded_vertices.add(u)
            return True
        return False

    # Unidireccional O(b^d) (lento para listas grande)
    def bfs(self, inicio, meta):
        # 1. Expandir el nodo de inicio para comenzar la búsqueda
        self.expandir_vertice(inicio) # Esto consulta la DB
        self.expandir_vertice(meta)

        if inicio == meta: return self.reconstruir_ruta(inicio, meta, {})

        cola = deque([inicio])
        visitados = {inicio}
        padres = {inicio: None}

        while cola:
            u = cola.popleft()
            
            # 2. Iterar sobre los vecinos de u que ya están en el grafo
            for v, attr in self.lista_adyacencia.get(u, []):
                if v not in visitados:
                    visitados.add(v)
                    padres[v] = (u, attr)
                    
                    if v == meta:
                        return self.reconstruir_ruta(inicio, meta, padres)
                    
                    cola.append(v)
                    
                    # 3. ¡EXPANDIR EL NODO RECIÉN AÑADIDO!
                    # Para que en la siguiente iteración el BFS pueda explorar más profundo.
                    self.expandir_vertice(v) # Esto podría consultar la DB si 'v' no estaba cargado
        
        return None # No se encontró la ruta
    
    def reconstruir_ruta(self, inicio, meta, padres):
        camino_inverso = []
        actual = meta
        
        # Detenemos el bucle cuando 'actual' es el nodo de inicio
        while actual != inicio: 
            # 'padres[actual]' ahora contiene la tupla (actor_anterior, movie_id)
            anterior, attr = padres[actual]
            # Guardamos la tupla en formato (Origen, Película, Destino)
            # Lo hacemos en orden inverso para luego invertir la lista.
            camino_inverso.append({'anterior': anterior, 'attr': attr, 'actual': actual})
            actual = anterior # Movemos el puntero al actor anterior

        # 2. Invertir la lista para obtener el orden correcto (inicio a meta)
        # y retornar el formato de "Aristas" que solicitaste.
        return camino_inverso[::-1]
    

    # Bidireccional O(2 b^d/2) (mucho más rápido)
    def bfs_bidireccional(self, inicio, meta):
        # 1. Expansión inicial de ambos nodos
        self.expandir_vertice(inicio)
        self.expandir_vertice(meta)

        if inicio == meta:
            return [(inicio, None, meta)]

        # --- Estructuras para la búsqueda desde A (adelante) ---
        cola_a = deque([inicio])
        visitados_a = {inicio}
        padres_a = {inicio: None}

        # --- Estructuras para la búsqueda desde B (atrás) ---
        cola_b = deque([meta])
        visitados_b = {meta}
        padres_b = {meta: None}

        punto_encuentro = None

        while cola_a and cola_b:
            # --- Expandir un nivel desde A ---
            punto_encuentro = self._expandir_nivel(cola_a, visitados_a, padres_a, visitados_b)
            if punto_encuentro:
                break

            # --- Paso 2: Expandir un nivel desde B ---
            punto_encuentro = self._expandir_nivel(cola_b, visitados_b, padres_b, visitados_a)
            if punto_encuentro:
                break
        
        if punto_encuentro:
            return self._reconstruir_ruta_bidireccional(inicio, meta, punto_encuentro, padres_a, padres_b)
        
        return None # No se encontró la ruta

    def _expandir_nivel(self, cola, visitados_propios, padres_propios, visitados_oponente):
        # Procesa todos los nodos del nivel actual en la cola
        nodos_en_nivel = len(cola)
        for _ in range(nodos_en_nivel):
            u = cola.popleft()

            # Expande el nodo si es necesario (carga desde DB)
            self.expandir_vertice(u)

            for v, attr in self.lista_adyacencia.get(u, []):
                if v not in visitados_propios:
                    visitados_propios.add(v)
                    padres_propios[v] = (u, attr)
                    cola.append(v)
                    
                    # CONDICIÓN DE ENCUENTRO
                    if v in visitados_oponente:
                        # Hemos encontrado un nodo visitado por la otra búsqueda
                        return v # ¡Ruta encontrada!
        return None

    def _reconstruir_ruta_bidireccional(self, inicio, meta, punto_encuentro, padres_a, padres_b):
        # Reconstruye desde A hasta el punto de encuentro
        camino_a = []
        actual = punto_encuentro
        while actual != inicio:
            anterior, attr = padres_a[actual]
            camino_a.append((anterior, attr, actual))
            actual = anterior
        
        # Reconstruye desde B hasta el punto de encuentro
        camino_b = []
        actual = punto_encuentro
        while actual != meta:
            anterior, attr = padres_b[actual]
            camino_b.append((actual, attr, anterior))
            actual = anterior

        # Une los dos caminos (el de A va en orden inverso)
        return camino_a[::-1] + camino_b