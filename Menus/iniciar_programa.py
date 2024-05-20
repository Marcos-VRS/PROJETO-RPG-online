##################### INICIA O PROGRAMA ####################
class inicia_programa:
    import os

    def funcao_inciar_programa_gm(): ...

    def funcao_iniciar_programa_player(): ...

    os.system("cls")
    condicao_menu_inicio = True

    while condicao_menu_inicio:
        inicio = input(
            "ESCOLHA UMA DAS OPÇÕES:\n"
            "[0] GM                [1] PLAYER\n\n"
            "Escolher:"
        )
        if inicio == "0":
            funcao_inciar_programa_gm()
        if inicio == "1":
            funcao_iniciar_programa_player()
        else:
            continue
