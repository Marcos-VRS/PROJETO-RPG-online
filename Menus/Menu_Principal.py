"""
É o menu principal do jogo. Server para chamar as funções menu 
"""


class Menu:

    def menu_principal_ficha(self):
        import os

        validador_menu = True
        pergunta_sair = ""

        while validador_menu:
            os.system("cls")
            opcao_menu = input(
                "\n\nMENU PRINCIPAL\nDigite uma das  opções a seguir:\n\n"
                "[1] ATRIBUTOS\n"
                "[2] SUBATRIBUTOS\n"
                "[3] VANTAGENS\n"
                "[4] DESVANTAGENS\n"
                "[5] PERÍCIAS\n"
                "[6] INFORMAÇÕES EXTRAS\n"
                "[7] PRINTAR A FICHA\n"
                "[8] SALVAR FICHA\n"
                "[9] CARREGAR FICHA\n"
                "[0] SAIR\n\n"
                "Selecionar:"
            )
            if opcao_menu == "1":
                from menu_atributo import Atributos

                menu_atributos = Atributos()
                menu_atributos.menu_atributos()  # Chamar função que chama o menu de atributos
                validador_menu = False

            elif opcao_menu == "2":
                ...  # Chamar função equivalente
            elif opcao_menu == "3":
                ...
            elif opcao_menu == "4":
                ...
            elif opcao_menu == "5":
                from menu_pericia import Pericias

                menu_pericias = Pericias()
                menu_pericias.menu_pericias()

            elif opcao_menu == "6":
                ...
            elif opcao_menu == "7":
                ...
            elif opcao_menu == "8":
                ...
            elif opcao_menu == "9":
                ...
            elif opcao_menu == "0":
                pergunta_sair = input(
                    "\n\nTem certeza que deseja sair?\n Digite [s] para sair."
                )
                if pergunta_sair.lower() == "s":
                    print("\n\nSAINDO DO PROGRAMA\n\n")
                    validador_menu = False
                else:
                    continue
            else:
                print(
                    "Desculpe. Você não digitou uma opção válida\n"
                    "Digite um dos valores do menu sem digitar os []."
                )
