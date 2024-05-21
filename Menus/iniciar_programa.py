##################### INICIA O PROGRAMA ####################
class inicia_programa:
    import os

    os.system("cls")

    def inicio_do_programa():
        condicao_menu_inicio = True
        while condicao_menu_inicio:
            inicio = input(
                "ESCOLHA UMA DAS OPÇÕES:\n"
                "[0] GM                [1] PLAYER\n\n"
                "Escolher:"
            )
            if inicio == "0":
                ...
            if inicio == "1":
                ...
            else:
                continue

    inicio_do_programa()
