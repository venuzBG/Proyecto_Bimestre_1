import base64
import io

import flet as ft
import igraph as ig
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.patches import Circle
from src.grafos.grafo import Grafo


class FletGraphApp:
    """
    Interfaz Flet para el proyecto de rutas en grafos.

    - Usa el TDA Grafo (Nodo, Arista, Grafo) para cargar el grafo y
      ejecutar BFS / DFS.
    - Usa igraph + matplotlib para DIBUJAR:
        * el grafo original
        * el árbol BFS / DFS
    - Muestra los resultados (distancias, padres, rutas, deepest_path, tiempo, etc.)
      en un panel con scroll.
    """

    def __init__(self):
        self.grafo: Grafo | None = None
        self.bfs_result = None
        self.dfs_result = None

        # Controles que se rellenan en main()
        self.start_dd: ft.Dropdown | None = None
        self.run_bfs_btn: ft.ElevatedButton | None = None
        self.run_dfs_btn: ft.ElevatedButton | None = None
        self.info_panel: ft.Container | None = None
        self.graph_image: ft.Image | None = None
        self.tree_image: ft.Image | None = None

    # ==========================================================
    #   FUNCIÓN PRINCIPAL DE FLET
    # ==========================================================
    def main(self, page: ft.Page):
        page.title = "Rutas en Grafos - BFS y DFS (Flet)"
        page.horizontal_alignment = "center"
        page.vertical_alignment = "start"
        page.padding = 20
        page.theme_mode = ft.ThemeMode.LIGHT

        # ---------- Selector de archivo para el grafo ----------
        file_picker = ft.FilePicker(
            on_result=lambda e: self.on_file_selected(e, page)
        )
        page.overlay.append(file_picker)

        load_btn = ft.ElevatedButton(
            "Cargar grafo (.txt)",
            icon=ft.Icons.UPLOAD_FILE,
            on_click=lambda _: file_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["txt"],
            ),
        )

        # ---------- Controles para BFS/DFS ----------
        self.start_dd = ft.Dropdown(
            label="Nodo inicio (start)",
            options=[],
            disabled=True,
            width=250,
        )

        self.run_bfs_btn = ft.ElevatedButton(
            "Ejecutar BFS (campus)",
            icon=ft.Icons.TRAVEL_EXPLORE,
            disabled=True,
            on_click=lambda _: self.run_bfs_campus(page),
        )

        self.run_dfs_btn = ft.ElevatedButton(
            "Ejecutar DFS (campus)",
            icon=ft.Icons.FUNCTIONS,
            disabled=True,
            on_click=lambda _: self.run_dfs_campus(page),
        )

        # ---------- Imágenes del grafo y árbol ----------
        self.graph_image = ft.Image(
            width=380,
            height=260,
            fit=ft.ImageFit.CONTAIN,
        )

        self.tree_image = ft.Image(
            width=380,
            height=260,
            fit=ft.ImageFit.CONTAIN,
        )


        # ---------- Panel de resultados con scroll ----------
        self.info_panel = ft.Container(
            content=ft.Column([], scroll=ft.ScrollMode.AUTO),
            height=220,
            width=800,
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            padding=10,
        )

        # ---------- Layout general ----------
        page.add(
            ft.Column(
                controls=[
                    load_btn,
                    ft.Row(
                        [self.start_dd, self.run_bfs_btn, self.run_dfs_btn],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Grafo cargado", weight=ft.FontWeight.BOLD),
                                    self.graph_image,
                                    ft.TextButton(
                                        "Ver grafo en grande",
                                        on_click=self.show_graph_dialog, 
                                    ),
                                ],
                                spacing=5,
                            ),
                            ft.Column(
                                [
                                    ft.Text("Árbol BFS/DFS", weight=ft.FontWeight.BOLD),
                                    self.tree_image,
                                    ft.TextButton(
                                        "Ver árbol en grande",
                                        on_click=self.show_tree_dialog, 
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                        spacing=20,
                    ),
                    ft.Text(
                        "Resultados del algoritmo:",
                        weight=ft.FontWeight.BOLD,
                        size=14,
                    ),
                    self.info_panel,
                ],
                spacing=20,
                width=900,
            )
        )


    # ==========================================================
    #   CALLBACK: CUANDO SE SELECCIONA EL ARCHIVO DEL GRAFO
    # ==========================================================
    def on_file_selected(self, e: ft.FilePickerResultEvent, page: ft.Page):
        if not e.files:
            return

        path = e.files[0].path

        try:
            # Usa tu método de clase: Grafo.desde_archivo(...)
            self.grafo = Grafo.desde_archivo(path, dirigido=False, separador=",")
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error al cargar grafo: {ex}"))
            page.snack_bar.open = True
            page.update()
            return

        # Llenar dropdown de nodos de inicio
        nodos = self.grafo.nodos()
        self.start_dd.options = [ft.dropdown.Option(n) for n in nodos]
        self.start_dd.value = nodos[0] if nodos else None
        self.start_dd.disabled = False

        # Habilitar botones
        self.run_bfs_btn.disabled = False
        self.run_dfs_btn.disabled = False

        # Dibujar grafo
        self.update_graph_image(page)

        page.snack_bar = ft.SnackBar(ft.Text(f"Grafo cargado desde: {path}"))
        page.snack_bar.open = True
        page.update()

    # ==========================================================
    #   EJECUCIÓN BFS / DFS EN MODO CAMPUS
    # ==========================================================
    def run_bfs_campus(self, page: ft.Page):
        if not self.grafo or not self.start_dd.value:
            return

        start = self.start_dd.value

        # 1) BFS completo desde start (sin goal específico)
        res = self.grafo.bfs(start, goal=None)

        # 2) Detectar salidas automáticamente
        salidas = self.grafo.nodos_salida(prefijo="Salida")
        salidas_reach = [s for s in salidas if s in res["distances"]]

        if not salidas_reach:
            page.snack_bar = ft.SnackBar(
                ft.Text("No se encontró ninguna salida alcanzable desde el nodo de inicio.")
            )
            page.snack_bar.open = True
            page.update()
            return

        # 3) Escoger la salida más cercana (distancia mínima)
        salida_cercana = min(salidas_reach, key=lambda s: res["distances"][s])

        # 4) Reconstruir ruta hacia esa salida
        ruta = self.grafo._reconstruir_camino(res["parents"], start, salida_cercana)

        # 5) Guardar información para mostrarse / dibujar árbol
        res["start"] = start
        res["goal"] = salida_cercana
        res["path"] = ruta
        self.bfs_result = res

        # 6) Actualizar panel de resultados + árbol
        self.show_bfs_info(page, res)
        self.update_tree_image(page, res, algorithm="bfs")

    def run_dfs_campus(self, page: ft.Page):
        if not self.grafo or not self.start_dd.value:
            return

        start = self.start_dd.value

        # Igual que en BFS: usamos BFS para definir salida más cercana
        bfs_res = self.grafo.bfs(start, goal=None)
        salidas = self.grafo.nodos_salida(prefijo="Salida")
        salidas_reach = [s for s in salidas if s in bfs_res["distances"]]

        if not salidas_reach:
            page.snack_bar = ft.SnackBar(
                ft.Text("No se encontró ninguna salida alcanzable desde el nodo de inicio.")
            )
            page.snack_bar.open = True
            page.update()
            return

        salida_cercana = min(salidas_reach, key=lambda s: bfs_res["distances"][s])

        # DFS con esa salida como goal
        res = self.grafo.dfs(start, goal=salida_cercana)
        res["start"] = start
        res["goal"] = salida_cercana
        self.dfs_result = res

        self.show_dfs_info(page, res)
        self.update_tree_image(page, res, algorithm="dfs")

    # ==========================================================
    #   PANEL DE RESULTADOS (TEXTO CON SCROLL)
    # ==========================================================
    def show_bfs_info(self, page: ft.Page, res):
        start = res["start"]
        goal = res["goal"]
        tiempo = res["time"]

        col: ft.Column = self.info_panel.content
        col.controls.clear()

        col.controls.append(ft.Text("ALGORITMO BFS", weight=ft.FontWeight.BOLD))
        col.controls.append(ft.Text(f"start = {start}    finish = {goal}"))
        col.controls.append(ft.Text(f"tiempo de ejecución = {tiempo:.6f} s"))
        col.controls.append(ft.Text(""))

        col.controls.append(
            ft.Text(
                "distancias (nodo → distancia desde start):",
                weight=ft.FontWeight.BOLD,
            )
        )
        for n, d in res["distances"].items():
            col.controls.append(ft.Text(f"  {n}: {d}"))

        col.controls.append(ft.Text(""))
        col.controls.append(
            ft.Text(
                "padres (nodo ← padre en árbol BFS):",
                weight=ft.FontWeight.BOLD,
            )
        )
        for n, p in res["parents"].items():
            col.controls.append(ft.Text(f"  {n} ← {p}"))

        col.controls.append(ft.Text(""))
        col.controls.append(
            ft.Text(
                "ruta más corta start → finish:",
                weight=ft.FontWeight.BOLD,
            )
        )
        path = res.get("path")
        if path is None:
            col.controls.append(ft.Text("  No existe ruta entre start y goal."))
        else:
            col.controls.append(ft.Text("  " + " -> ".join(path)))

        page.update()

    def show_dfs_info(self, page: ft.Page, res):
        start = res["start"]
        goal = res["goal"]
        tiempo = res["time"]

        col: ft.Column = self.info_panel.content
        col.controls.clear()

        col.controls.append(ft.Text("ALGORITMO DFS", weight=ft.FontWeight.BOLD))
        col.controls.append(ft.Text(f"start = {start}    goal = {goal}"))
        col.controls.append(ft.Text(f"tiempo de ejecución = {tiempo:.6f} s"))
        col.controls.append(ft.Text(""))

        col.controls.append(
            ft.Text(
                "padres (nodo ← padre en árbol DFS):",
                weight=ft.FontWeight.BOLD,
            )
        )
        for n, p in res["parents"].items():
            col.controls.append(ft.Text(f"  {n} ← {p}"))

        col.controls.append(ft.Text(""))
        col.controls.append(
            ft.Text(
                "ruta DFS start → goal:",
                weight=ft.FontWeight.BOLD,
            )
        )
        dfs_path = res.get("dfs_path")
        if dfs_path is None:
            col.controls.append(ft.Text("  No existe ruta entre start y goal."))
        else:
            col.controls.append(ft.Text("  " + " -> ".join(dfs_path)))

        col.controls.append(ft.Text(""))
        col.controls.append(
            ft.Text(
                "camino de mayor profundidad (deepest_path):",
                weight=ft.FontWeight.BOLD,
            )
        )
        deepest = res.get("deepest_path")
        if deepest is None:
            col.controls.append(
                ft.Text("  No se pudo determinar el camino más profundo.")
            )
        else:
            col.controls.append(ft.Text("  " + " -> ".join(deepest)))

        page.update()

    # ==========================================================
    #   DIBUJO DEL GRAFO Y DEL ÁRBOL (IMÁGENES PNG → base64)
    # ==========================================================
    @staticmethod
    def _normalized_layout(layout):
        xs = [c[0] for c in layout]
        ys = [c[1] for c in layout]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        def nx(x): return (x - min_x) / (max_x - min_x + 1e-9)
        def ny(y): return (y - min_y) / (max_y - min_y + 1e-9)

        return [(nx(x), ny(y)) for x, y in layout]


    @staticmethod
    def _figure_to_base64(fig: Figure) -> str:
        """Convierte una figura de matplotlib a string base64 (PNG)."""
        buf = io.BytesIO()
        canvas = FigureCanvasAgg(fig)
        canvas.draw()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    # ---------- helpers nuevos ----------

    def _graph_base64(self, figsize=(4, 3)):
        """Dibuja el grafo del campus y devuelve la imagen en base64."""
        if not self.grafo:
            return ""

        nombres = self.grafo.nodos()
        name_to_idx = {name: i for i, name in enumerate(nombres)}

        edges = set()
        for u in self.grafo.nodos():
            for v, _ in self.grafo.vecinos(u):
                par = tuple(sorted((name_to_idx[u], name_to_idx[v])))
                edges.add(par)

        g_ig = ig.Graph()
        g_ig.add_vertices(len(nombres))
        if edges:
            g_ig.add_edges(list(edges))
        g_ig.vs["label"] = nombres

        layout = g_ig.layout("kk")
        coords = self._normalized_layout(layout)
        r = 0.04

        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_subplot(111)
        ax.set_axis_off()

        # aristas
        for u, v in g_ig.get_edgelist():
            x1, y1 = coords[u]
            x2, y2 = coords[v]
            dx, dy = x2 - x1, y2 - y1
            length = (dx**2 + dy**2) ** 0.5 or 1.0
            ux, uy = dx / length, dy / length
            sx1, sy1 = x1 + ux * r, y1 + uy * r
            sx2, sy2 = x2 - ux * r, y2 - uy * r
            ax.plot([sx1, sx2], [sy1, sy2], color="gray", linewidth=1.8)

        # nodos
        for vid in range(g_ig.vcount()):
            x, y = coords[vid]
            circle = Circle((x, y), r, facecolor="#8ce99a",
                            edgecolor="black", linewidth=1.8)
            ax.add_patch(circle)
            label = g_ig.vs[vid]["label"]
            ax.text(x, y, label, ha="center", va="center", fontsize=9)

        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-0.1, 1.1)
        ax.set_aspect("equal")

        return self._figure_to_base64(fig)

    def _tree_base64(self, res: dict, figsize=(4, 3)):
        """Dibuja el árbol BFS/DFS a partir del dict de padres y devuelve base64."""
        parents = res.get("parents")
        if not parents:
            return ""

        # raíz
        root_node = None
        for n, p in parents.items():
            if p is None:
                root_node = n
                break
        if root_node is None:
            return ""

        nodes = list(parents.keys())
        name_to_idx = {name: i for i, name in enumerate(nodes)}
        edges = []
        for n, p in parents.items():
            if p is not None:
                edges.append((name_to_idx[p], name_to_idx[n]))

        tree_g = ig.Graph()
        tree_g.add_vertices(len(nodes))
        if edges:
            tree_g.add_edges(edges)
        tree_g.vs["label"] = nodes

        layout = tree_g.layout("tree", root=[name_to_idx[root_node]])
        coords = self._normalized_layout(layout)
        # invertimos Y para que la raíz quede arriba
        coords = [(x, 1 - y) for x, y in coords]
        r = 0.05

        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_subplot(111)
        ax.set_axis_off()

        # aristas
        for u, v in tree_g.get_edgelist():
            x1, y1 = coords[u]
            x2, y2 = coords[v]
            dx, dy = x2 - x1, y2 - y1
            length = (dx**2 + dy**2) ** 0.5 or 1.0
            ux, uy = dx / length, dy / length
            sx1, sy1 = x1 + ux * r, y1 + uy * r
            sx2, sy2 = x2 - ux * r, y2 - uy * r
            ax.plot([sx1, sx2], [sy1, sy2], color="black", linewidth=1.8)

        # nodos
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

        return self._figure_to_base64(fig)

    # ---------- versiones pequeñas para la pantalla principal ----------

    def update_graph_image(self, page: ft.Page):
        if not self.graph_image:
            return
        self.graph_image.src_base64 = self._graph_base64(figsize=(4, 3))
        page.update()

    def update_tree_image(self, page: ft.Page, res: dict, algorithm: str):
        if not self.tree_image:
            return
        self.tree_image.src_base64 = self._tree_base64(res, figsize=(4, 3))
        page.update()

    
        # ==========================================================
    #   DIÁLOGOS: VER GRAFO / ÁRBOL EN GRANDE
    # ==========================================================

    def _close_dialog(self, e: ft.ControlEvent):
        page = e.page
        if page.dialog:
            page.dialog.open = False
            page.update()

    def show_graph_dialog(self, e: ft.ControlEvent):
        """Muestra el grafo en una ventana más grande."""
        page = e.page

        if not self.grafo:
            # Mensaje rojo cuando aún no hay grafo cargado
            page.snack_bar = ft.SnackBar(
                ft.Text("Grafo aún no cargado. Carga un archivo .txt primero.")
            )
            page.snack_bar.open = True
            page.update()
            return

        img = ft.Image(width=900, height=600, fit=ft.ImageFit.CONTAIN)
        img.src_base64 = self._graph_base64(figsize=(8, 6))

        dlg = ft.AlertDialog(
            title=ft.Text("Grafo del campus"),
            content=img,
            actions=[
                ft.TextButton("Cerrar", on_click=self._close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dlg
        dlg.open = True
        page.update()

    def show_tree_dialog(self, e: ft.ControlEvent):
        """Muestra el árbol BFS/DFS actual en una ventana más grande."""
        page = e.page

        # Usa el último resultado disponible, BFS o DFS
        res = self.bfs_result or self.dfs_result
        if not res:
            # Mensaje rojo cuando aún no se ha ejecutado BFS/DFS
            page.snack_bar = ft.SnackBar(
                ft.Text("Árbol aún no cargado. Ejecuta BFS o DFS primero.")
            )
            page.snack_bar.open = True
            page.update()
            return

        img = ft.Image(width=900, height=600, fit=ft.ImageFit.CONTAIN)
        img.src_base64 = self._tree_base64(res, figsize=(8, 6))

        dlg = ft.AlertDialog(
            title=ft.Text("Árbol BFS/DFS"),
            content=img,
            actions=[
                ft.TextButton("Cerrar", on_click=self._close_dialog)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        page.dialog = dlg
        dlg.open = True
        page.update()


def main(page: ft.Page):
    app = FletGraphApp()
    app.main(page)


if __name__ == "__main__":
    ft.app(target=main)
