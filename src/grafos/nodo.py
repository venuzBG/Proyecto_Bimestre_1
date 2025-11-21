class Nodo:
    """
    Representa un nodo (vértice) del grafo.

    - id:  identificador del nodo (string)
    - data: información extra opcional (no la usas ahora,
      pero te permite guardar más datos en el futuro).
    """
    def __init__(self, id_nodo, data=None):
        self.id = id_nodo
        self.data = data  # información extra opcional

    def __repr__(self):
        return f"Nodo({self.id!r})"

