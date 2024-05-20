class Atributos:

    def menu_atributos():  # função que chama menu de atributos
        import os
        import math

        st = 10
        dx = 10
        iq = 10
        ht = 10
        xp_gasto_st = 0
        xp_gasto_dx = 0
        xp_gasto_iq = 0
        xp_gasto_ht = 0
        incremento_st = 0
        pergunta_sair_atributos = ""
        opcao_menu_atributos = ""
        validador_menu_atributo = True

        while validador_menu_atributo:  # condição para o menu continuar rodando.

            os.system("cls")
            print(
                "--" * 15,
                "\n\n"
                "FICHA ATUAL:\n"
                f"\nST:{st:.0f} (+{xp_gasto_st}) \n"
                f"DX:{dx:.0f} (+{xp_gasto_dx}) \n"
                f"IQ:{iq:.0f} (+{xp_gasto_iq}) \n"
                f"HT:{ht:.0f} (+{xp_gasto_ht}) \n\n",
            )
            opcao_menu_atributos = input(
                "Digite o número corresponde ao atributo que deseja alterar:\n"
                "[1] ST\n"
                "[2] DX\n"
                "[3] IQ\n"
                "[4] HT\n"
                "[5] Voltar\n\n"
                "Selecionar: "
            )

            if opcao_menu_atributos == "1":
                incremento_st = input("Quantos pontos deseja gastar em ST: ")
                if incremento_st.isdigit() or incremento_st.lstrip("-").isdigit():
                    xp_gasto_st += int(incremento_st)
                    st += int(incremento_st) / 10
                else:
                    continue
            elif opcao_menu_atributos == "2":
                incremento_dx = input("Quantos pontos deseja gastar em DX: ")
                if incremento_dx.isdigit() or incremento_dx.lstrip("-").isdigit():
                    xp_gasto_dx += int(incremento_dx)
                    dx += int(incremento_dx) / 20
                else:
                    continue

            elif opcao_menu_atributos == "3":
                incremento_iq = input("Quantos pontos deseja gastar em IQ: ")
                if incremento_iq.isdigit() or incremento_iq.lstrip("-").isdigit():
                    xp_gasto_iq += int(incremento_iq)
                    iq += int(incremento_iq) / 20
                else:
                    continue

            elif opcao_menu_atributos == "4":
                incremento_ht = input("Quantos pontos deseja gastar em HT: ")
                if incremento_ht.isdigit() or incremento_ht.lstrip("-").isdigit():
                    xp_gasto_ht += int(incremento_ht)
                    ht += int(incremento_ht) / 10
                else:
                    continue

            elif opcao_menu_atributos == "5":

                from menu_principal import Menu

                menu_principal = Menu()
                menu_principal.menu_principal_ficha()
                validador_menu_atributo = False

            else:
                continue

    menu_atributos()
