##################### INICIA O PROGRAMA ####################
class IniciaPrograma:
    import os

    os.system("cls")

    # INICIA O PROGRAMA
    def inicio_do_programa():

        # VARIÁVEIS
        condicao_menu_inicio = True

        # MENU DA TELA DE INÍCIO
        while condicao_menu_inicio:
            inicio = input(
                "ESCOLHA UMA DAS OPÇÕES:\n"
                "[0] GM                [1] PLAYER\n\n"
                "Escolher:"
            )

            # CASO SEJA O GM
            if inicio == "0":
                from menu_set_gm import MenuSetGM

                menu_set_gm = MenuSetGM()
                menu_set_gm.menu_set_gm()

            # CASO SEJA UM JOGADOR (TROCAR DEPOIS PARA O MENU_SET_PLAYER)
            if inicio == "1":
                from menu_personagem import MenuPersonagem

                menu_personagem = MenuPersonagem()
                menu_personagem.menu_principal_ficha()
            else:
                continue

    inicio_do_programa()
