# import flet as ft
# from src.ui_flet.App_flet import main as flet_main
# from src.ui.app import run_app as tkinter_app

# def menu():
#     print("Seleccione interfaz:")
#     print("1. Interfaz FLET")
#     print("2. Interfaz Tkinter")
#     x = input("Opción: ")
#     return x

# if __name__ == "__main__":
#     opcion = menu()
#     if opcion == "1":
#         ft.app(target=flet_main)
#     else:
#         tkinter_app()

import flet as ft
from src.ui_flet.App_flet import main as flet_main

if __name__ == "__main__":
    ft.app(target=flet_main)



# from src.ui.app import run_app
# from src.ui_flet.App_flet import run_app_flet as flet_main
# import flet as ft

# if __name__ == "__main__":
#     ft.app(target=flet_main)
    
# # if __name__ == "__main__":
# #     run_app()

