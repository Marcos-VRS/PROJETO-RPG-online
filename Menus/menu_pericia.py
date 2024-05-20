"""
É o menu de perícias do jogo. 
"""


class Pericias:
    def menu_pericias(self):
        import os

        validador_menu_pericias = True
        pergunta_sair_pericias = ""
        pericia = ["Briga", "Innate attack", "Acrobatics"]
        dificuldade = ["DX/E", "DX/E", "DX/H"]
        custo = ["4", "1", "1"]
        nh = ["16", "12", "10"]
        while validador_menu_pericias:
            os.system("cls")
            print(f"Perícias", "-" * 30, "C/NH")
            # for i, pericia in enumerate(pericia):

            #     print(
            #         f"[{i+1}]  {pericia} {dificuldade[i]:<24}{custo[i]}",
            #         "/",
            #         f"{nh[i]} ",
            #     )
            opcao_menu_pericias = input(
                "\n\nMENUS DAS PERÍCIAS:\n"
                "[i]nserir    [a]pagar    [e]ditar    [v]oltar\n\n"
                "Selecionar: "
            )
            if opcao_menu_pericias.lower() == "i":
                ...
            elif opcao_menu_pericias.lower() == "a":
                ...
            elif opcao_menu_pericias.lower() == "e":
                ...
            elif opcao_menu_pericias.lower() == "v":
                from menu_principal import MenuPrincipal

                menu_principal = MenuPrincipal()
                menu_principal.menu_principal_ficha()
                validador_menu_pericias = False
