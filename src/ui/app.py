import tkinter as tk
from tkinter import ttk, messagebox

from src.grafos.grafo import Grafo

# 🔹 Librería para dibujar el árbol en una ventana moderna
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle


class GraphGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rutas en Grafos - BFS y DFS")
        self.root.geometry("900x600")

        # Estilo más moderno (ttk)
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        # Grafo de ejemplo pequeño
        self.grafo = self._construir_grafo_campus()

        # Posiciones de nodos para el grafo principal
        self.positions = {
            "Aula_101": (120, 250),
            "Aula_102": (120, 350),
            "Hall":     (300, 300),
            "Pasillo":  (500, 300),
            "Laboratorio": (700, 230),
            "Salida":      (700, 370),
        }

        # id_nodo -> {"oval": id_canvas, "label": id_canvas}
        self.node_items = {}

        # Últimos resultados
        self.last_bfs = None
        self.last_dfs = None
        self.last_algorithm = None  # "bfs" o "dfs"

        self._build_ui()
        self._draw_graph()

    # ---------- Construcción de UI ----------

    def _build_ui(self):
        # Frame principal con margen
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas donde se dibuja el grafo
        self.canvas = tk.Canvas(main_frame, bg="#f8f9fa", highlightthickness=0)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame de botones en la parte inferior
        controls = ttk.Frame(main_frame)
        controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Label(
            controls,
            text="Controles:",
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.btn_bfs = ttk.Button(controls, text="BFS", width=10,
                                  command=self._on_bfs_clicked)
        self.btn_bfs.pack(side=tk.LEFT, padx=5)

        self.btn_dfs = ttk.Button(controls, text="DFS", width=10,
                                  command=self._on_dfs_clicked)
        self.btn_dfs.pack(side=tk.LEFT, padx=5)

        self.btn_tree = ttk.Button(controls, text="Ver árbol", width=12,
                                   command=self._on_tree_clicked)
        self.btn_tree.pack(side=tk.LEFT, padx=5)

    # ---------- Grafo de ejemplo pequeño ----------

    def _construir_grafo_campus(self):
        """
        Grafo pequeño para ejemplo:
        Aula_101 --\
                     \
        Aula_102 ---- Hall ---- Pasillo ---- Laboratorio
                                  \
                                   \---- Salida
        """
        g = Grafo(dirigido=False)

        g.add_arista("Aula_101", "Hall")
        g.add_arista("Aula_102", "Hall")
        g.add_arista("Hall", "Pasillo")
        g.add_arista("Pasillo", "Laboratorio")
        g.add_arista("Pasillo", "Salida")

        return g

    # ---------- Dibujo del grafo principal ----------

    def _draw_graph(self):
        self.canvas.delete("all")
        self.node_items.clear()

        # Dibujar aristas (una vez por cada par)
        dibujadas = set()
        for u in self.grafo.nodos():
            for v, _ in self.grafo.vecinos(u):
                edge_key = tuple(sorted([u, v]))
                if edge_key in dibujadas:
                    continue
                dibujadas.add(edge_key)

                x1, y1 = self.positions[u]
                x2, y2 = self.positions[v]
                self.canvas.create_line(x1, y1, x2, y2, width=2, fill="#6c757d")

        # Dibujar nodos
        radius = 26
        for node_id, (x, y) in self.positions.items():
            oval = self.canvas.create_oval(
                x - radius, y - radius, x + radius, y + radius,
                fill="#dee2e6", outline="#343a40", width=2
            )
            label = self.canvas.create_text(
                x, y, text=node_id, font=("Segoe UI", 9)
            )
            self.node_items[node_id] = {"oval": oval, "label": label}

    def _reset_colors(self):
        for node_id, items in self.node_items.items():
            self.canvas.itemconfig(items["oval"], fill="#dee2e6")

    def _color_node(self, node_id, color):
        if node_id in self.node_items:
            self.canvas.itemconfig(self.node_items[node_id]["oval"], fill=color)

    # ---------- Botones ----------

    def _on_bfs_clicked(self):
        self._ask_start_node(algorithm="bfs")

    def _on_dfs_clicked(self):
        self._ask_start_node(algorithm="dfs")

    def _on_tree_clicked(self):
        if self.last_algorithm == "bfs" and self.last_bfs is not None:
            parents = self.last_bfs["parents"]
            title = "Árbol BFS"
        elif self.last_algorithm == "dfs" and self.last_dfs is not None:
            parents = self.last_dfs["parents"]
            title = "Árbol DFS"
        else:
            messagebox.showinfo(
                "Sin recorrido",
                "Primero ejecuta BFS o DFS para generar un árbol."
            )
            return

        self._show_tree_window(parents, title)

    # ---------- Ventana para seleccionar nodo start ----------

    def _ask_start_node(self, algorithm):
        window = tk.Toplevel(self.root)
        window.title(f"Seleccionar nodo de inicio ({algorithm.upper()})")
        window.resizable(False, False)

        frame = ttk.Frame(window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Nodo de inicio:").pack(pady=(0, 5))

        nodo_var = tk.StringVar()
        nodos = self.grafo.nodos()
        if not nodos:
            messagebox.showerror("Error", "El grafo no tiene nodos.")
            window.destroy()
            return

        nodo_var.set(nodos[0])

        combo = ttk.Combobox(frame, textvariable=nodo_var,
                             values=nodos, state="readonly", width=18)
        combo.pack(pady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        def iniciar():
            start_node = nodo_var.get()
            window.destroy()
            if algorithm == "bfs":
                self._run_bfs(start_node)
            else:
                self._run_dfs(start_node)

        def cancelar():
            window.destroy()

        ttk.Button(btn_frame, text="Iniciar", command=iniciar, width=10)\
            .pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=cancelar, width=10)\
            .pack(side=tk.LEFT, padx=5)

    # ---------- BFS / DFS + animación ----------

    def _run_bfs(self, start):
        try:
            self.last_bfs = self.grafo.bfs(start)
            self.last_algorithm = "bfs"
        except ValueError as e:
            messagebox.showerror("Error BFS", str(e))
            return

        self._reset_colors()
        self._color_node(start, "#0d6efd")   # azul
        order = self.last_bfs["order"]
        self._animate_visit(order, index=0, color="#51cf66")  # verde

    def _run_dfs(self, start):
        try:
            self.last_dfs = self.grafo.dfs(start)
            self.last_algorithm = "dfs"
        except ValueError as e:
            messagebox.showerror("Error DFS", str(e))
            return

        self._reset_colors()
        self._color_node(start, "#0d6efd")   # azul
        order = self.last_dfs["order"]
        self._animate_visit(order, index=0, color="#ffa94d")  # naranja

    def _animate_visit(self, order, index, color):
        if index >= len(order):
            return
        node_id = order[index]
        self._color_node(node_id, color)
        # siguiente nodo después de 500 ms
        self.root.after(500, lambda: self._animate_visit(order, index + 1, color))

    # ---------- Ventana para dibujar el árbol con matplotlib ----------

    def _show_tree_window(self, parents, title):
        """
        Dibuja el árbol de padres en una nueva ventana usando matplotlib,
        con un estilo tipo diagrama de árbol (como tu imagen).
        """
        # Encontrar raíz (nodo cuyo padre es None)
        root = None
        for node, padre in parents.items():
            if padre is None:
                root = node
                break
        if root is None:
            messagebox.showerror("Error", "No se pudo determinar la raíz del árbol.")
            return

        # Construir estructura de hijos y profundidades
        children = {n: [] for n in parents}
        depth = {root: 0}
        for nodo, padre in parents.items():
            if padre is not None:
                children[padre].append(nodo)
                depth[nodo] = depth[padre] + 1

        max_depth = max(depth.values())

        # Agrupar nodos por nivel
        levels = {}
        for nodo, d in depth.items():
            levels.setdefault(d, []).append(nodo)

        # Posiciones (x,y) normalizadas
        positions = {}
        for d, nodes_at_level in levels.items():
            n = len(nodes_at_level)
            for i, nodo in enumerate(nodes_at_level):
                x = (i + 1) / (n + 1)            # espaciado horizontal
                y = -(d + 1)                    # niveles hacia abajo
                positions[nodo] = (x, y)

        # Crear ventana y figura matplotlib
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("600x400")

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_axis_off()

        # Dibujar aristas
        for padre, hijos in children.items():
            x1, y1 = positions[padre]
            for hijo in hijos:
                x2, y2 = positions[hijo]
                ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.5)

        # Dibujar nodos
        for nodo, (x, y) in positions.items():
            circle = Circle((x, y), 0.05, facecolor="white",
                            edgecolor="black", linewidth=1.5)
            ax.add_patch(circle)
            ax.text(x, y, str(nodo), ha="center", va="center", fontsize=9)

        ax.set_xlim(0, 1)
        ax.set_ylim(-(max_depth + 2), 0)

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


def run_app():
    root = tk.Tk()
    app = GraphGUI(root)
    root.mainloop()
