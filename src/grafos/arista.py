class Arista:
    """
    Representa una arista entre dos nodos del grafo.

    No es estrictamente necesaria para el algoritmo,
    pero sirve para guardar un registro más claro de las conexiones.
    """
    def __init__(self, origen, destino, peso: float = 1):
        self.origen = origen
        self.destino = destino
        self.peso = peso

    def __repr__(self):
        return f"Arista({self.origen!r} -> {self.destino!r}, peso={self.peso})"

