from collections import deque
import time

from src.grafos.nodo import Nodo
from src.grafos.arista import Arista


class Grafo:
    """
    TAD Grafo basado en lista de adyacencia.
    """
    def __init__(self, dirigido=False):
        self.dirigido = dirigido
        self._nodos = {}          # id -> Nodo
        self._adyacencia = {}     # id -> lista de (vecino, peso)
        self._aristas = []        # lista de Arista

    # ---------- Gestión de nodos y aristas ----------

    def add_nodo(self, id_nodo, data=None):
        if id_nodo not in self._nodos:
            self._nodos[id_nodo] = Nodo(id_nodo, data)
            self._adyacencia[id_nodo] = []
        return self._nodos[id_nodo]

    def add_arista(self, origen, destino, peso=1):
        self.add_nodo(origen)
        self.add_nodo(destino)

        self._adyacencia[origen].append((destino, peso))
        self._aristas.append(Arista(origen, destino, peso))

        if not self.dirigido:
            self._adyacencia[destino].append((origen, peso))
            self._aristas.append(Arista(destino, origen, peso))

    def nodos(self):
        return list(self._nodos.keys())

    def vecinos(self, id_nodo):
        return self._adyacencia.get(id_nodo, [])

    # ---------- BFS ----------

    def bfs(self, start, goal=None):
        """
        BFS(start, goal=None) -> dict con:
          - distances: dict nodo -> distancia (nº de aristas)
          - parents: dict nodo -> padre en el árbol BFS
          - path: ruta más corta start->goal (si goal no es None y hay camino)
          - tree: Grafo que representa el árbol BFS
          - order: lista de nodos en el orden en que fueron visitados (para animación)
          - time: tiempo de ejecución
        """
        if start not in self._nodos:
            raise ValueError("start no existe en el grafo.")

        t0 = time.perf_counter()

        distancias = {start: 0}
        padres = {start: None}
        cola = deque([start])
        aristas_arbol = []
        orden_visita = []  # para animación

        while cola:
            actual = cola.popleft()
            orden_visita.append(actual)

            for vecino, _ in self.vecinos(actual):
                if vecino not in distancias:
                    distancias[vecino] = distancias[actual] + 1
                    padres[vecino] = actual
                    aristas_arbol.append((actual, vecino))
                    cola.append(vecino)

        # Si se pasa goal, reconstruimos ruta
        ruta = None
        if goal is not None:
            ruta = self._reconstruir_camino(padres, start, goal)

        arbol_bfs = self._construir_arbol_desde_aristas(start, aristas_arbol)

        t1 = time.perf_counter()

        return {
            "distances": distancias,
            "parents": padres,
            "path": ruta,
            "tree": arbol_bfs,
            "order": orden_visita,
            "time": t1 - t0
        }

    # ---------- DFS ----------

    def dfs(self, start, goal=None):
        """
        DFS(start, goal=None) -> dict con:
          - parents: dict nodo -> padre en el árbol DFS
          - tree: Grafo que representa el árbol DFS
          - dfs_path: ruta encontrada hacia goal (si se pasa goal)
          - deepest_path: camino más profundo desde start en el árbol DFS
          - order: lista de nodos en el orden de visita (para animación)
          - time: tiempo de ejecución
        """
        if start not in self._nodos:
            raise ValueError("start no existe en el grafo.")

        t0 = time.perf_counter()

        padres = {start: None}
        profundidad = {start: 0}
        aristas_arbol = []
        orden_visita = []

        def _dfs(u):
            orden_visita.append(u)
            for v, _ in self.vecinos(u):
                if v not in padres:
                    padres[v] = u
                    profundidad[v] = profundidad[u] + 1
                    aristas_arbol.append((u, v))
                    _dfs(v)

        _dfs(start)

        ruta_dfs = None
        if goal is not None:
            ruta_dfs = self._reconstruir_camino(padres, start, goal)

        nodo_mas_profundo = max(profundidad, key=lambda n: profundidad[n])
        deepest_path = self._reconstruir_camino(padres, start, nodo_mas_profundo)

        arbol_dfs = self._construir_arbol_desde_aristas(start, aristas_arbol)

        t1 = time.perf_counter()

        return {
            "parents": padres,
            "tree": arbol_dfs,
            "dfs_path": ruta_dfs,
            "deepest_path": deepest_path,
            "order": orden_visita,
            "time": t1 - t0
        }

    # ---------- Utilidades internas ----------

    @staticmethod
    def _reconstruir_camino(padres, inicio, fin):
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
        arbol = Grafo(dirigido=True)
        arbol.add_nodo(raiz)
        for u, v in aristas:
            arbol.add_arista(u, v)
        return arbol
    
    # ---------- Construcción de grafo desde archivo ----------

    @classmethod
    def desde_archivo(cls, ruta, dirigido=False, separador=","):
        """
        Carga un grafo desde un archivo de texto.
        Cada línea debe tener el formato:
            origen,separador,destino,separador,peso
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
                        peso = 1

                    grafo.add_arista(origen, destino, peso)

            return grafo

        except FileNotFoundError:
            raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

        except Exception as e:
            raise Exception(f"Error al leer el archivo {ruta}: {e}")
        
        
    # ---------- Utilidades de análisis de la estructura del grafo ----------

    def grado(self, id_nodo):
        """
        Devuelve el grado (número de vecinos) de un nodo.
        """
        return len(self._adyacencia.get(id_nodo, []))

    def nodos_hoja(self):
        """
        Nodos con grado 1 (típicamente extremos de pasillos).
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
