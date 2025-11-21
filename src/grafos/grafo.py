from collections import deque
import time

from src.grafos.nodo import Nodo
from src.grafos.arista import Arista


class Grafo:
    """
    TAD Grafo basado en lista de adyacencia.

    Internamente se guardan:
    - _nodos:   id_nodo -> objeto Nodo
    - _adyacencia: id_nodo -> lista de (vecino, peso)
    - _aristas: lista de objetos Arista
    """

    # ----------------------------------------------------------
    #  CONSTRUCTOR
    # ----------------------------------------------------------
    def __init__(self, dirigido: bool = False):
        # Si dirigido = False, cada arista se guarda en ambos sentidos
        self.dirigido = dirigido
        self._nodos: dict[str, Nodo] = {}
        self._adyacencia: dict[str, list[tuple[str, float]]] = {}
        self._aristas: list[Arista] = []

    # ----------------------------------------------------------
    #  GESTIÓN DE NODOS Y ARISTAS
    # ----------------------------------------------------------
    def add_nodo(self, id_nodo, data=None) -> Nodo:
        """
        Crea el nodo si no existe y lo devuelve.

        id_nodo: identificador del nodo (ej: 'Aula_101')
        data:    información extra opcional
        """
        if id_nodo not in self._nodos:
            self._nodos[id_nodo] = Nodo(id_nodo, data)
            self._adyacencia[id_nodo] = []
        return self._nodos[id_nodo]

    def add_arista(self, origen, destino, peso: float = 1):
        """
        Agrega una arista (origen -> destino) al grafo.

        - Si el grafo es no dirigido, también se agrega (destino -> origen).
        - Se guardan objetos Arista solo como registro extra.
        """
        # Aseguramos que los nodos existan
        self.add_nodo(origen)
        self.add_nodo(destino)

        # Arista origen -> destino
        self._adyacencia[origen].append((destino, peso))
        self._aristas.append(Arista(origen, destino, peso))

        # Si no es dirigido, agregamos la arista inversa
        if not self.dirigido:
            self._adyacencia[destino].append((origen, peso))
            self._aristas.append(Arista(destino, origen, peso))

    def nodos(self):
        """Devuelve la lista de ids de nodos del grafo."""
        return list(self._nodos.keys())

    def vecinos(self, id_nodo):
        """
        Devuelve la lista de vecinos de un nodo:
        lista de (id_vecino, peso)
        """
        return self._adyacencia.get(id_nodo, [])

    # ----------------------------------------------------------
    #  BREADTH-FIRST SEARCH (BFS)
    # ----------------------------------------------------------
    def bfs(self, start, goal=None):
        """
        BFS(start, goal=None) -> dict con:

        - distances: dict nodo -> distancia en nº de aristas desde 'start'
        - parents:   dict nodo -> padre en el árbol BFS
        - path:      ruta más corta start->goal (si se pasa goal y hay camino)
        - tree:      Grafo que representa el árbol BFS (dirigido)
        - order:     lista de nodos en el orden de visita (para animación)
        - time:      tiempo de ejecución en segundos
        """
        if start not in self._nodos:
            raise ValueError("start no existe en el grafo.")

        t0 = time.perf_counter()

        # Inicialización de estructuras
        distancias = {start: 0}
        padres = {start: None}
        cola = deque([start])
        aristas_arbol = []  # aristas que formarán el árbol BFS
        orden_visita = []   # para animar el recorrido

        # Búsqueda BFS clásica
        while cola:
            actual = cola.popleft()
            orden_visita.append(actual)

            for vecino, _ in self.vecinos(actual):
                if vecino not in distancias:
                    distancias[vecino] = distancias[actual] + 1
                    padres[vecino] = actual
                    aristas_arbol.append((actual, vecino))
                    cola.append(vecino)

        # Si se pasa un goal, reconstruimos la ruta mínima
        ruta = None
        if goal is not None:
            ruta = self._reconstruir_camino(padres, start, goal)

        # Árbol BFS como un nuevo Grafo dirigido
        arbol_bfs = self._construir_arbol_desde_aristas(start, aristas_arbol)

        t1 = time.perf_counter()

        return {
            "distances": distancias,
            "parents": padres,
            "path": ruta,
            "tree": arbol_bfs,
            "order": orden_visita,
            "time": t1 - t0,
        }

    # ----------------------------------------------------------
    #  DEPTH-FIRST SEARCH (DFS)
    # ----------------------------------------------------------
    def dfs(self, start, goal=None):
        """
        DFS(start, goal=None) -> dict con:

          - parents:      dict nodo -> padre en el árbol DFS
          - tree:         Grafo que representa el árbol DFS
          - dfs_path:     ruta encontrada hacia goal (si se pasa goal)
          - deepest_path: camino más profundo desde start en el árbol DFS
          - order:        lista de nodos en el orden de visita (para animación)
          - time:         tiempo de ejecución
        """
        if start not in self._nodos:
            raise ValueError("start no existe en el grafo.")

        t0 = time.perf_counter()

        padres = {start: None}
        profundidad = {start: 0}  # nivel de cada nodo
        aristas_arbol = []
        orden_visita = []

        def _dfs(u):
            """Función recursiva para la búsqueda en profundidad."""
            orden_visita.append(u)
            for v, _ in self.vecinos(u):
                if v not in padres:
                    padres[v] = u
                    profundidad[v] = profundidad[u] + 1
                    aristas_arbol.append((u, v))
                    _dfs(v)

        _dfs(start)

        # Ruta desde start hasta goal (si se especifica y es alcanzable)
        ruta_dfs = None
        if goal is not None:
            ruta_dfs = self._reconstruir_camino(padres, start, goal)

        # Buscamos el nodo más profundo para construir deepest_path
        nodo_mas_profundo = max(profundidad, key=lambda n: profundidad[n])
        deepest_path = self._reconstruir_camino(padres, start, nodo_mas_profundo)

        # Árbol DFS como nuevo grafo dirigido
        arbol_dfs = self._construir_arbol_desde_aristas(start, aristas_arbol)

        t1 = time.perf_counter()

        return {
            "parents": padres,
            "tree": arbol_dfs,
            "dfs_path": ruta_dfs,
            "deepest_path": deepest_path,
            "order": orden_visita,
            "time": t1 - t0,
        }

    # ----------------------------------------------------------
    #  UTILIDADES INTERNAS (no se llaman desde fuera)
    # ----------------------------------------------------------
    @staticmethod
    def _reconstruir_camino(padres, inicio, fin):
        """
        Reconstruye el camino inicio -> fin usando el diccionario de padres.

        Si 'fin' no está en padres o el camino no empieza en 'inicio',
        devuelve None.
        """
        if fin not in padres:
            return None

        camino = []
        actual = fin
        while actual is not None:
            camino.append(actual)
            actual = padres[actual]

        camino.reverse()
        if not camino or camino[0] != inicio:
            return None
        return camino

    @staticmethod
    def _construir_arbol_desde_aristas(raiz, aristas):
        """
        Construye un nuevo Grafo dirigido que representa un árbol
        a partir de la lista de aristas (padre, hijo) y la raíz.
        """
        arbol = Grafo(dirigido=True)
        arbol.add_nodo(raiz)
        for u, v in aristas:
            arbol.add_arista(u, v)
        return arbol

    # ----------------------------------------------------------
    #  CONSTRUCCIÓN DE GRAFO DESDE ARCHIVO .TXT
    # ----------------------------------------------------------
    @classmethod
    def desde_archivo(cls, ruta, dirigido=False, separador=","):
        """
        Carga un grafo desde un archivo de texto.

        Cada línea (no vacía ni comentario) debe tener el formato:
            origen{sep}destino{sep}peso

        Ejemplo (con separador = ','):
            Aula_101,Hall,1
        Si no se especifica peso, se asume 1.
        """
        grafo = cls(dirigido=dirigido)

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()

                    # Saltar líneas vacías o comentarios
                    if not linea or linea.startswith("#"):
                        continue

                    partes = linea.split(separador)

                    if len(partes) < 2:
                        raise ValueError(f"Línea inválida: {linea}")

                    origen = partes[0].strip()
                    destino = partes[1].strip()

                    # Si no hay peso, se asume 1
                    if len(partes) >= 3:
                        try:
                            peso = float(partes[2])
                        except ValueError:
                            raise ValueError(f"Peso inválido en línea: {linea}")
                    else:
                        peso = 1.0

                    grafo.add_arista(origen, destino, peso)

            return grafo

        except FileNotFoundError:
            raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

        except Exception as e:
            # Reempaquetamos cualquier otro error con contexto
            raise Exception(f"Error al leer el archivo {ruta}: {e}")

    # ----------------------------------------------------------
    #  UTILIDADES DE ANÁLISIS DE LA ESTRUCTURA DEL GRAFO
    # ----------------------------------------------------------
    def grado(self, id_nodo):
        """
        Devuelve el grado (número de vecinos) de un nodo.
        En un grafo no dirigido es el nº de aristas incidentes.
        """
        return len(self._adyacencia.get(id_nodo, []))

    def nodos_hoja(self):
        """
        Devuelve los nodos con grado 1 (hojas).

        En el contexto del campus suelen ser:
        - extremos de pasillos
        - aulas en el borde
        - salidas
        """
        return [n for n in self._adyacencia if self.grado(n) == 1]

    def nodos_salida(self, prefijo="Salida"):
        """
        Devuelve los nodos considerados 'salidas' en el campus.

        Estrategia:
        - Deben ser hojas (grado 1).
        - Su nombre debe empezar por el prefijo (por defecto 'Salida').
        """
        hojas = self.nodos_hoja()
        return [n for n in hojas if str(n).startswith(prefijo)]
