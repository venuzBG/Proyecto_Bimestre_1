import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

import igraph as ig
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Circle

from src.grafos.grafo import Grafo


class GraphApp:
    """
    App principal:
      - Usa tu TDA Grafo (Nodo, Arista, Grafo) para el modelo y BFS/DFS.
      - Usa igraph SOLO para el layout y dibujo.
      - Carga por defecto Campus.txt (si existe).
      - Muestra árbol BFS/DFS con métricas: distancias, padres, ruta, deepest_path, tiempo.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Rutas en Grafos - BFS y DFS")
        self.root.geometry("900x600")

        # Estilos
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))

        # ==== Modelo (TDA Grafo) ====
        self.grafo = self._cargar_grafo_por_defecto()

        # ==== igraph auxiliar ====
        self.ig_graph = None
        self.name_to_idx = {}
        self.idx_to_name = {}
        self.layout = None

        # Colores nodos
        self.base_color = "#ffc078"      # naranja suave
        self.node_colors = []

        # Resultados recorridos
        self.last_bfs = None   # dict con resultado BFS
        self.last_dfs = None   # dict con resultado DFS
        self.last_algorithm = None  # "bfs" o "dfs"

        # Construir UI
        self._build_ui()

        # Sincronizar igraph y dibujar
        self._sync_igraph_from_model()
        self._draw_graph()

    # ==========================================================
    #   Carga de grafo
    # ==========================================================

    def _cargar_grafo_por_defecto(self) -> Grafo:
        """
        Intenta cargar Campus.txt de la raíz del proyecto.
        Si no existe, usa el grafo de ejemplo pequeño.
        """
        project_root = Path(__file__).resolve().parents[2]
        campus_file = project_root / "Campus.txt"

        if campus_file.exists():
            try:
                return Grafo.desde_archivo(str(campus_file), dirigido=False, separador=",")
            except Exception as e:
                messagebox.showwarning(
                    "Error cargando Campus.txt",
                    f"No se pudo leer Campus.txt:\n{e}\nSe usará el grafo de ejemplo."
                )

        # fallback
        return self._construir_grafo_ejemplo()

    def _construir_grafo_ejemplo(self) -> Grafo:
        g = Grafo(dirigido=False)
        g.add_arista("Aula_101", "Hall")
        g.add_arista("Aula_102", "Hall")
        g.add_arista("Hall", "Pasillo")
        g.add_arista("Pasillo", "Laboratorio")
        g.add_arista("Pasillo", "Salida")
        return g

    def _load_graph_from_file(self, path: str):
        try:
            self.grafo = Grafo.desde_archivo(path, dirigido=False, separador=",")
        except Exception as e:
            messagebox.showerror("Error al cargar grafo", str(e))
            return

        self._sync_igraph_from_model()
        self._draw_graph()
        self.last_bfs = self.last_dfs = None
        self.last_algorithm = None
        messagebox.showinfo("Grafo cargado", f"Grafo cargado desde:\n{path}")

    # ==========================================================
    #   Conversión a igraph
    # ==========================================================

    def _sync_igraph_from_model(self):
        nombres = self.grafo.nodos()
        if not nombres:
            self.ig_graph = ig.Graph()
            self.name_to_idx = {}
            self.idx_to_name = {}
            self.layout = None
            self.node_colors = []
            return

        self.name_to_idx = {name: i for i, name in enumerate(nombres)}
        self.idx_to_name = {i: name for name, i in self.name_to_idx.items()}

        edges = set()
        for u in self.grafo.nodos():
            for v, _ in self.grafo.vecinos(u):
                par = tuple(sorted((self.name_to_idx[u], self.name_to_idx[v])))
                edges.add(par)

        g_ig = ig.Graph()
        g_ig.add_vertices(len(nombres))
        if edges:
            g_ig.add_edges(list(edges))
        g_ig.vs["label"] = nombres

        self.ig_graph = g_ig
        self.layout = self.ig_graph.layout("kk")
        self.node_colors = [self.base_color] * self.ig_graph.vcount()

    # ==========================================================
    #   UI
    # ==========================================================

    def _build_ui(self):
        # Menú
        menubar = tk.Menu(self.root)
        menu_archivo = tk.Menu(menubar, tearoff=0)
        menu_archivo.add_command(label="Cargar grafo...", command=self._on_load_graph)
        menu_archivo.add_separator()
        menu_archivo.add_command(label="Salir", command=self.root.quit)
        menubar.add_cascade(label="Archivo", menu=menu_archivo)
        self.root.config(menu=menubar)

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Figura para grafo principal
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_axis_off()

        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas_fig.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Controles abajo
        controls = ttk.Frame(main_frame)
        controls.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Label(controls, text="Controles:").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(controls, text="BFS", width=10,
                   command=lambda: self._ask_start_goal("bfs")).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="DFS", width=10,
                   command=lambda: self._ask_start_goal("dfs")).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls, text="Ver árbol", width=12,
                   command=self._on_tree_clicked).pack(side=tk.LEFT, padx=5)

    # ==========================================================
    #   Dibujo del grafo principal
    # ==========================================================

    def _normalized_layout(self, layout):
        if layout is None or len(layout) == 0:
            return []

        xs = [coord[0] for coord in layout]
        ys = [coord[1] for coord in layout]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        def nx(x): return (x - min_x) / (max_x - min_x + 1e-9)
        def ny(y): return (y - min_y) / (max_y - min_y + 1e-9)

        return [(nx(x), ny(y)) for x, y in layout]

    def _draw_graph(self):
        self.ax.clear()
        self.ax.set_axis_off()

        if self.ig_graph is None or self.ig_graph.vcount() == 0:
            self.canvas_fig.draw()
            return

        coords = self._normalized_layout(self.layout)
        r = 0.04  # radio

        # Aristas: desde borde a borde
        for (u, v) in self.ig_graph.get_edgelist():
            x1, y1 = coords[u]
            x2, y2 = coords[v]
            dx, dy = x2 - x1, y2 - y1
            length = (dx**2 + dy**2) ** 0.5 or 1.0
            ux, uy = dx / length, dy / length

            sx1, sy1 = x1 + ux * r, y1 + uy * r
            sx2, sy2 = x2 - ux * r, y2 - uy * r

            self.ax.plot([sx1, sx2], [sy1, sy2], color="#495057", linewidth=2)

        # Nodos
        for vid in range(self.ig_graph.vcount()):
            x, y = coords[vid]
            circle = Circle((x, y), r,
                            facecolor=self.node_colors[vid],
                            edgecolor="#343a40", linewidth=2)
            self.ax.add_patch(circle)
            label = self.ig_graph.vs[vid]["label"]
            self.ax.text(x, y, label, ha="center", va="center", fontsize=9)

        self.ax.set_xlim(-0.1, 1.1)
        self.ax.set_ylim(-0.1, 1.1)
        self.ax.set_aspect("equal")
        self.canvas_fig.draw()

    def _reset_colors(self):
        self.node_colors = [self.base_color] * len(self.node_colors)
        self._draw_graph()

    def _set_node_color(self, node_name, color):
        idx = self.name_to_idx.get(node_name)
        if idx is not None:
            self.node_colors[idx] = color

    # ==========================================================
    #   Eventos de menú / botones
    # ==========================================================

    def _on_load_graph(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de grafo",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")]
        )
        if not path:
            return
        self._load_graph_from_file(path)

    def _on_tree_clicked(self):
        if self.last_algorithm == "bfs" and self.last_bfs is not None:
            self._show_tree_window(self.last_bfs, "bfs")
        elif self.last_algorithm == "dfs" and self.last_dfs is not None:
            self._show_tree_window(self.last_dfs, "dfs")
        else:
            messagebox.showinfo("Sin recorrido", "Ejecuta primero BFS o DFS.")
            return

    # ==========================================================
    #   Selección de start y goal
    # ==========================================================

    def _ask_start_goal(self, algorithm: str):
        window = tk.Toplevel(self.root)
        window.title(f"Parámetros {algorithm.upper()}")
        window.resizable(False, False)

        frame = ttk.Frame(window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        nodos = self.grafo.nodos()
        if not nodos:
            messagebox.showerror("Error", "El grafo no tiene nodos.")
            window.destroy()
            return

        start_var = tk.StringVar(value=nodos[0])
        goal_var = tk.StringVar(value=nodos[0])

        ttk.Label(frame, text="Nodo inicio (start):").pack(anchor="w")
        ttk.Combobox(frame, textvariable=start_var, values=nodos,
                     state="readonly", width=20).pack(pady=(0, 5))

        ttk.Label(frame, text="Nodo objetivo (goal/finish):").pack(anchor="w")
        ttk.Combobox(frame, textvariable=goal_var, values=nodos,
                     state="readonly", width=20).pack(pady=(0, 5))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        def iniciar():
            start = start_var.get()
            goal = goal_var.get()
            window.destroy()
            if algorithm == "bfs":
                self._run_bfs(start, goal)
            else:
                self._run_dfs(start, goal)

        def cancelar():
            window.destroy()

        ttk.Button(btn_frame, text="Iniciar", width=10,
                   command=iniciar).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", width=10,
                   command=cancelar).pack(side=tk.LEFT, padx=5)

    # ==========================================================
    #   BFS / DFS + animación
    # ==========================================================

    def _run_bfs(self, start, goal):
        try:
            res = self.grafo.bfs(start, goal)
        except ValueError as e:
            messagebox.showerror("Error BFS", str(e))
            return

        res["start"] = start
        res["goal"] = goal
        self.last_bfs = res
        self.last_algorithm = "bfs"

        self._reset_colors()
        self._set_node_color(start, "#0d6efd")  # azul start
        self._draw_graph()

        order = res["order"]
        self._animate_visit(order, 0, "#51cf66")  # verde BFS

    def _run_dfs(self, start, goal):
        try:
            res = self.grafo.dfs(start, goal)
        except ValueError as e:
            messagebox.showerror("Error DFS", str(e))
            return

        res["start"] = start
        res["goal"] = goal
        self.last_dfs = res
        self.last_algorithm = "dfs"

        self._reset_colors()
        self._set_node_color(start, "#0d6efd")  # azul start
        self._draw_graph()

        order = res["order"]
        # 💠 DFS en celeste (como pediste)
        self._animate_visit(order, 0, "#4dabf7")

    def _animate_visit(self, order, index, color):
        if index >= len(order):
            return
        node_name = order[index]
        self._set_node_color(node_name, color)
        self._draw_graph()
        self.root.after(500, lambda: self._animate_visit(order, index + 1, color))

    # ==========================================================
    #   Ventana del árbol + métricas BFS / DFS
    # ==========================================================

    def _show_tree_window(self, result: dict, algorithm: str):
        """
        Dibuja el árbol (BFS/DFS) y muestra:
          - tiempo
          - distancias (solo BFS)
          - padres
          - ruta más corta (BFS) / ruta DFS
          - deepest_path (DFS)
        """
        parents = result["parents"]

        # raíz
        root_node = None
        for node, padre in parents.items():
            if padre is None:
                root_node = node
                break
        if root_node is None:
            messagebox.showerror("Error", "No se pudo determinar la raíz del árbol.")
            return

        nodes = list(parents.keys())
        name_to_idx = {name: i for i, name in enumerate(nodes)}
        edges = []
        for nodo, padre in parents.items():
            if padre is not None:
                edges.append((name_to_idx[padre], name_to_idx[nodo]))

        tree_g = ig.Graph()
        tree_g.add_vertices(len(nodes))
        if edges:
            tree_g.add_edges(edges)
        tree_g.vs["label"] = nodes

        layout = tree_g.layout("tree", root=[name_to_idx[root_node]])
        coords = self._normalized_layout(layout)
        # 🔁 Invertimos Y para que la raíz quede arriba, no abajo
        coords = [(x, 1 - y) for x, y in coords]

        # Ventana
        if algorithm == "bfs":
            title = "Árbol BFS"
        else:
            title = "Árbol DFS"

        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("700x500")

        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)

        # Figura
        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)
        ax.set_axis_off()

        r = 0.045

        # Aristas
        for u, v in tree_g.get_edgelist():
            x1, y1 = coords[u]
            x2, y2 = coords[v]
            dx, dy = x2 - x1, y2 - y1
            length = (dx**2 + dy**2) ** 0.5 or 1.0
            ux, uy = dx / length, dy / length

            sx1, sy1 = x1 + ux * r, y1 + uy * r
            sx2, sy2 = x2 - ux * r, y2 - uy * r

            ax.plot([sx1, sx2], [sy1, sy2], color="black", linewidth=1.8)

        # Nodos
        for vid in range(tree_g.vcount()):
            x, y = coords[vid]
            circle = Circle((x, y), r, facecolor="white",
                            edgecolor="black", linewidth=1.8)
            ax.add_patch(circle)
            label = tree_g.vs[vid]["label"]
            ax.text(x, y, label, ha="center", va="center", fontsize=9)

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, 1.1)
        ax.set_aspect("equal")

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # ---- Panel de texto con las consideraciones del algoritmo ----
        text = tk.Text(frame, height=10, font=("Consolas", 9))
        text.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=False)

        start = result.get("start")
        goal = result.get("goal")
        tiempo = result.get("time", 0.0)

        if algorithm == "bfs":
            text.insert(tk.END, "ALGORITMO BFS\n\n")
            text.insert(tk.END, f"start = {start}   finish = {goal}\n")
            text.insert(tk.END, f"tiempo de ejecución = {tiempo:.6f} s\n\n")

            text.insert(tk.END, "distancias (nodo -> distancia desde start):\n")
            for n, d in result["distances"].items():
                text.insert(tk.END, f"  {n}: {d}\n")

            text.insert(tk.END, "\npadres (nodo <- padre en árbol BFS):\n")
            for n, p in result["parents"].items():
                text.insert(tk.END, f"  {n} <- {p}\n")

            text.insert(tk.END, "\nruta más corta start → goal:\n")
            path = result.get("path")
            if path is None:
                text.insert(tk.END, "  No existe ruta entre start y goal.\n")
            else:
                text.insert(tk.END, "  " + " -> ".join(path) + "\n")

        else:  # DFS
            text.insert(tk.END, "ALGORITMO DFS\n\n")
            text.insert(tk.END, f"start = {start}   goal = {goal}\n")
            text.insert(tk.END, f"tiempo de ejecución = {tiempo:.6f} s\n\n")

            text.insert(tk.END, "padres (nodo <- padre en árbol DFS):\n")
            for n, p in result["parents"].items():
                text.insert(tk.END, f"  {n} <- {p}\n")

            text.insert(tk.END, "\nruta encontrada por DFS (start → goal):\n")
            dfs_path = result.get("dfs_path")
            if dfs_path is None:
                text.insert(tk.END, "  No existe ruta entre start y goal.\n")
            else:
                text.insert(tk.END, "  " + " -> ".join(dfs_path) + "\n")

            text.insert(tk.END, "\ncamino de mayor profundidad desde start (deepest_path):\n")
            deepest = result.get("deepest_path")
            if deepest is None:
                text.insert(tk.END, "  No se pudo determinar el camino más profundo.\n")
            else:
                text.insert(tk.END, "  " + " -> ".join(deepest) + "\n")

        text.config(state=tk.DISABLED)


def run_app():
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()
