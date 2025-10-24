from collections import deque, defaultdict

class Graphs:
    """
    Representación de un Grafo No Dirigido usando Lista de Adyacencia.
    """
    def __init__(self):
        # El diccionario almacena la lista de adyacencia.
        # {vertice: [vecino1, vecino2, ...]}
        # defaultdict facilita agregar nuevos vértices sin inicialización manual.
        self.lista_adyacencia = defaultdict(list)
        self.num_vertices = 0
        
    def agregar_vertice(self, vertice):
        """Agrega un vértice si no existe."""
        if vertice not in self.lista_adyacencia:
            self.lista_adyacencia[vertice] = []
            self.num_vertices += 1

    def agregar_arista(self, u, v):
        """
        Agrega una arista entre u y v.
        Asume un grafo NO DIRIGIDO, por lo que agrega la conexión en ambas direcciones.
        """
        # Asegura que ambos vértices existan en el grafo
        self.agregar_vertice(u)
        self.agregar_vertice(v)
        
        # Agrega la arista. Evita duplicados, aunque la lista puede manejarlos si fuera necesario
        if v not in self.lista_adyacencia[u]:
            self.lista_adyacencia[u].append(v)
        if u not in self.lista_adyacencia[v]:
            self.lista_adyacencia[v].append(u)

    def obtener_vecinos(self, vertice):
        """Retorna la lista de vecinos de un vértice."""
        return self.lista_adyacencia.get(vertice, [])
    
    def __str__(self):
        """Representación legible del grafo."""
        output = "Grafo ({} Vértices):\n".format(self.num_vertices)
        for u, vecinos in self.lista_adyacencia.items():
            output += f"  {u}: {vecinos}\n"
        return output

    def bfs(self, inicio):
        """
        Realiza la Búsqueda a lo Ancho (BFS) desde un vértice de inicio.
        """
        if inicio not in self.lista_adyacencia:
            print(f"Error: El vértice de inicio '{inicio}' no existe.")
            return []

        # 1. Inicializa la cola y el conjunto de visitados
        cola = deque([inicio])
        visitados = {inicio}
        orden_recorrido = []

        # 2. Bucle principal de BFS
        while cola:
            # Desencola el vértice actual
            u = cola.popleft()
            orden_recorrido.append(u)
            
            # 3. Explora todos los vecinos
            for v in self.lista_adyacencia[u]:
                if v not in visitados:
                    visitados.add(v)
                    cola.append(v)
        
        return orden_recorrido
    
    def dfs_recursivo(self, inicio):
        """
        Inicia la Búsqueda en Profundidad (DFS) usando una función auxiliar recursiva.
        """
        if inicio not in self.lista_adyacencia:
            print(f"Error: El vértice de inicio '{inicio}' no existe.")
            return []
        
        visitados = set()
        orden_recorrido = []
        
        def _dfs_aux(u):
            """Función auxiliar que realiza la recursión."""
            visitados.add(u)
            orden_recorrido.append(u)
            
            # Recorre los vecinos de forma recursiva
            for v in self.lista_adyacencia[u]:
                if v not in visitados:
                    _dfs_aux(v)
        
        _dfs_aux(inicio)
        return orden_recorrido
    
    def dfs_iterativo(self, inicio):
        """
        Realiza la Búsqueda en Profundidad (DFS) usando una Pila explícita.
        """
        if inicio not in self.lista_adyacencia:
            print(f"Error: El vértice de inicio '{inicio}' no existe.")
            return []
            
        # 1. Inicializa la Pila (una lista simple en Python) y el conjunto de visitados
        pila = [inicio]
        visitados = {inicio}
        orden_recorrido = []
        
        # 2. Bucle principal de DFS
        while pila:
            # Saca (pop) el último elemento (comportamiento de Pila LIFO)
            u = pila.pop()
            orden_recorrido.append(u)
            
            # 3. Explora los vecinos (NOTA: se recomienda iterar en orden inverso
            #    si se desea simular exactamente el orden de la recursión, pero
            #    para la funcionalidad básica, este orden está bien)
            for v in reversed(self.lista_adyacencia[u]):
                if v not in visitados:
                    visitados.add(v)
                    pila.append(v)
                    
        return orden_recorrido