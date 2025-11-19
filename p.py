from src.grafos.grafo import Grafo
g = Grafo.desde_archivo("Campus.txt", dirigido=False, separador=",")
print(g.lista_ady)
