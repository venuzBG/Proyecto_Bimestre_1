class Arista:
    """
    Representa una arista entre dos nodos.
    """
    def __init__(self, origen, destino, peso=1):
        self.origen = origen
        self.destino = destino
        self.peso = peso

    def __repr__(self):
        return f"Arista({self.origen!r} -> {self.destino!r}, peso={self.peso})"
