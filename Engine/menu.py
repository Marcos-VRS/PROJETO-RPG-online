class Menu:

    def menu_inicio_programa(self):

        # IMPORTS
        import os
        from menu import Menu

        # VARIÁVEIS
        condicao_menu_inicio = True
        menu = Menu()

        # MENU DA TELA DE INÍCIO
        while condicao_menu_inicio:
            os.system("cls")
            inicio = input(
                "ESCOLHA UMA DAS OPÇÕES:\n"
                "[0] GM                [1] PLAYER\n\n"
                "Escolher:"
            )

            # CASO SEJA O GM
            if inicio == "0":
                menu.menu_set_gm()

            # CASO SEJA UM JOGADOR (TROCAR DEPOIS PARA O MENU_SET_PLAYER)
            if inicio == "1":
                menu.menu_set_player()
            else:
                continue

    def menu_set_gm(self):
        # IMPORTS
        import os
        from banco_de_dados import BancoDeDadosCampanha
        from mensagens_sistema import MensagensSistema

        # VARIÁVEIS
        menu = Menu()
        banco_de_dados = BancoDeDadosCampanha()
        mensagem_sistema = MensagensSistema()
        condicao_menu_gm = True

        # MENU
        while condicao_menu_gm:

            os.system("cls")
            escolha = input(
                "O QUE DESEJA FAZER ?\n\n"
                "[1] Criar uma nova campanha\n"
                "[2] Carregar camapanha\n"
                "[3] Deletar campanha\n"
                "[4] Voltar\n\n"
                "Selecionar:"
            )

            if escolha == "1":
                menu.criar_nova_campanha()
            elif escolha == "2":
                ...
            elif escolha == "3":
                ...
            elif escolha == "4":
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para a TELA DE INÍCIO?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_inicio_programa,
                    menu.menu_set_gm,
                )

            else:
                continue

    def criar_nova_campanha(self):
        # IMPORTS
        import os
        from menu import Menu
        from banco_de_dados import BancoDeDadosCampanha
        from mensagens_sistema import MensagensSistema

        # VARIÁVEIS
        verificador_set_gm = True
        menu = Menu()
        banco_de_dados = BancoDeDadosCampanha()
        mensagem_sistema = MensagensSistema()

        # MENU QUE SETA OS DADOS DA CAMPANHA

        while verificador_set_gm:
            os.system("cls")
            # MENSAGEM DE SAUDAÇÃO
            print(
                "\nOk. Vamos definir as informações da campanha.\n\n"
                "-Digite [sair] a qualquer momento para retornar a tela inicial.\n\n"
                "-Caso erre ou deseje editar algum dado, no final haverá uma opção.\n"
            )
            # CONDIÇÕES DO WHILE
            verificador_tl_campanha = True
            verificador_pontos = True
            verificador_desv = True
            verificador_pergunta_final = True
            # NOME DA CAMPANHA
            nome_campanha = input("NOME DA CAMPANHA:\n")

            # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
            if nome_campanha.lower() == "sair":
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para o MENU DO GM ?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_set_gm,
                    menu.criar_nova_campanha,
                )

            # ---------------------------------------------------#

            # NÍVEL DE TECNOLOGIA DA CAMPANHA
            while verificador_tl_campanha:

                tl_campanha = input("\nNÍVEL DE TECNOLOGIA:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if tl_campanha.lower() == "sair":
                    opcao_sair = input(
                        "\n\nDeseja realmente voltar para o MENU DO GM ?\n"
                        "[s]im para voltar\n"
                        "[n]ão para ficar\n\n"
                        "Selecionar: "
                    )
                    mensagem_sistema.deseja_voltar(
                        opcao_sair,
                        menu.menu_set_gm,
                        menu.criar_nova_campanha,
                    )

                # TESTA SE O VALOR DE TL_CAMPANHA É UM NÚMERO
                elif tl_campanha.isdigit():
                    verificador_tl_campanha = False

            # ---------------------------------------------------#

            # QUANTIDADE DE PONTOS INICIAL DOS PERSONAGENS
            while verificador_pontos:

                pontos_campanha = input("\nPONTOS:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if pontos_campanha.lower() == "sair":
                    opcao_sair = input(
                        "\n\nDeseja realmente voltar para o MENU DO GM ?\n"
                        "[s]im para voltar\n"
                        "[n]ão para ficar\n\n"
                        "Selecionar: "
                    )
                    mensagem_sistema.deseja_voltar(
                        opcao_sair,
                        menu.menu_set_gm,
                        menu.criar_nova_campanha,
                    )

                # TESTA SE O VALOR DE PONTO_CAMAPANHA É UM NÚMERO
                elif pontos_campanha.isdigit():
                    verificador_pontos = False

            # ---------------------------------------------------#

            while verificador_desv:

                desvantagens_campanha = input("\nDESVANTAGENS:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if desvantagens_campanha.lower() == "sair":
                    opcao_sair = input(
                        "\n\nDeseja realmente voltar para o MENU DO GM ?\n"
                        "[s]im para voltar\n"
                        "[n]ão para ficar\n\n"
                        "Selecionar: "
                    )
                    mensagem_sistema.deseja_voltar(
                        opcao_sair,
                        menu.menu_set_gm,
                        menu.criar_nova_campanha,
                    )

                # TESTA SE O VALOR DE PONTO_CAMAPNHA É UM NÚMERO
                elif desvantagens_campanha.isdigit():
                    verificador_desv = False

            # VERIFICA SE OS DADOS QUE O GM SETOU ESTÃO CORRETOS
            while verificador_pergunta_final:

                pergunta_final = input(
                    "\n\nOs dados da campanha estão corretos?\n\n"
                    "Digite [s] para salvar os dados da campanha.\n"
                    "Digite [n] para preencher novamente os dados\n"
                    "Digite [sair] para voltar para a tela de início\n"
                )
                # CASO DESEJE SALVAR OS DADOS
                if pergunta_final.lower() == "s":
                    os.system("cls")
                    print(
                        f"\n-------CAMPANHA CRIADA COM SUCESSO----------\n\n"
                        f"\nNOME DA CAMPANHA: {nome_campanha}"
                        f"\nNÍVEL DE TECNOLOGIA: {tl_campanha}"
                        f"\nPONTOS: {pontos_campanha}"
                        f"\nDESVANTAGENS: {desvantagens_campanha}\n\n"
                    )

                    # CONDIÇÃO PARA SEGUIR PARA A PRÓXIMA TELA
                    tela_seguinte = input(
                        "\nDeseja prosseguir?\n\n"
                        "Caso digite [s] sua campanha será salva.\n"
                        "Caso ainda deseje alterar algum dando digite [n]\n"
                    )

                    # CASO DESEJE PROSSEGUIR
                    if tela_seguinte.lower() == "s":
                        banco_de_dados.criar_nova_campanha(
                            nome_campanha,
                            tl_campanha,
                            pontos_campanha,
                            desvantagens_campanha,
                        )

                    elif tela_seguinte.lower() == "n":
                        continue

                # CASO DESEJE PREENCHER NOVAMENTE
                elif pergunta_final.lower() == "n":
                    break

                # CASO DESEJE VOLTAR PARA A TELA INICIAL
                elif pergunta_final.lower() == "sair":
                    opcao_sair = input(
                        "\n\nDeseja realmente voltar para o MENU DO GM ?\n"
                        "[s]im para voltar\n"
                        "[n]ão para ficar\n\n"
                        "Selecionar: "
                    )
                    mensagem_sistema.deseja_voltar(
                        opcao_sair,
                        menu.menu_set_gm,
                        menu.criar_nova_campanha,
                    )
                else:
                    continue

            os.system("cls")

    def menu_set_player(self):

        # IMPORTS
        import os
        from mensagens_sistema import MensagensSistema
        from banco_de_dados import BancoDeDadosPersonagem

        # VARIÁVEIS
        menu = Menu()
        mensagem_sistema = MensagensSistema()
        banco_de_dados = BancoDeDadosPersonagem()

        condicao_menu_carregar_personagem = True

        # MENU
        while condicao_menu_carregar_personagem:

            os.system("cls")
            escolha = input(
                "O QUE DESEJA FAZER?\n\n"
                "[1] Criar um novo personagem\n"
                "[2] Carregar um personagem salvo\n"
                "[3] Editar personagem existente\n"
                "[4] Ver informações da campanha\n"
                "[5] voltar\n\n"
                "Selecionar:"
            )

            if escolha == "1":
                os.system("cls")
                nome_personagem = input("Digite o nome do personagem:\n")
                nome_player = input("Digite o seu nome:\n")

                while True:
                    prosseguir = input(
                        "\n\nVocê deseja criar o novo personagem:\n"
                        f"NOME: {nome_personagem}\n"
                        f"JOGADOR: {nome_player}\n\n"
                        "[s]im\n"
                        "[n]ão\n"
                        "Selecionar: "
                    )
                    nome_arquivo = nome_personagem + " - " + nome_player
                    banco_de_dados.criar_novo_personagem(nome_arquivo)
                    mensagem_sistema.deseja_prosseguir(
                        prosseguir,
                        menu.menu_principal_criacao_personagem,
                        menu.menu_set_player,
                    )

            elif escolha == "2":
                banco_de_dados.carregar_personagem()
            elif escolha == "3":
                ...
            elif escolha == "4":
                ...
            elif escolha == "5":
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para a TELA INICIAL?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_inicio_programa,
                    menu.menu_set_player,
                )
            else:
                continue

    def menu_principal_criacao_personagem(self):

        # IMPORTS
        import os

        from menu import Menu
        from mensagens_sistema import MensagensSistema

        # VARIÁVEIS
        validador_menu = True
        pergunta_sair = ""
        menu = Menu()
        mensagem_sistema = MensagensSistema()

        # MOSTRA O MENU DE OPÇÕES DO MENU PRINCIPAL
        while validador_menu:
            os.system("cls")
            opcao_menu = input(
                "\nAgora vamos criar um personagem. Preencha as informações"
                " dele utilizando os menus abaixo"
                "\n\nMENU PRINCIPAL\nDigite uma das  opções a seguir:\n\n"
                "[1] ATRIBUTOS\n"
                "[2] SUBATRIBUTOS\n"
                "[3] VANTAGENS\n"
                "[4] DESVANTAGENS\n"
                "[5] PERÍCIAS\n"
                "[6] INFORMAÇÕES EXTRAS\n"
                "[7] PRINTAR A FICHA\n"
                "[8] SALVAR FICHA\n"
                "[9] CARREGAR UMA FICHA EXISTENTE\n"
                "[SAIR] PARA VOLTAR PARA TELA INICIAL\n\n"
                "Selecionar:"
            )

            # 1 - ATRIBUTOS
            if opcao_menu == "1":
                menu.menu_atributos_criacao_personagem()
            # 2 - SUBATRIBUTOS
            elif opcao_menu == "2":
                ...  # Chamar função equivalente

            # 3 - VANTAGENS
            elif opcao_menu == "3":
                ...

            # 4 - DESVANTAGENS
            elif opcao_menu == "4":
                ...

            # 5 - PERÍCIAS
            elif opcao_menu == "5":
                menu.menu_pericias_criacao_personagem()

            # 6 - INFORMAÇÕES EXTRAS
            elif opcao_menu == "6":
                ...
            # 7 - PRINTAR A FICHA
            elif opcao_menu == "7":
                ...

            # 8 - SALVAR FICHA
            elif opcao_menu == "8":
                ...
            # 9 - CARREGAR UMA FICHA EXISTENTE
            elif opcao_menu == "9":
                ...

            # 0 - SAIR
            elif opcao_menu.lower() == "sair":
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para o Menu do jogador?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_set_player,
                    menu.menu_principal_criacao_personagem,
                )

            # DIGITAR UMA OPÇÃO INVÁLIDA
            else:
                menu.menu_principal_criacao_personagem()

    def menu_atributos_criacao_personagem(self):
        # IMPORTS
        import os
        import math
        import openpyxl
        from menu import Menu
        from mensagens_sistema import MensagensSistema

        # VARIÁVEIS
        tabela_atributos = openpyxl.Workbook()
        menu = Menu()
        mensagem_sistema = MensagensSistema()
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

        # MOSTRA OS ATRIBUTOS ATUAIS E O MENU PARA ALTERA-LOS
        while validador_menu_atributo:
            os.system("cls")

            # ATRIBUTOS ATUAIS
            print(
                "--" * 15,
                "\n\n"
                "FICHA ATUAL:\n"
                f"\nST:{st:.0f} (+{xp_gasto_st}) \n"
                f"DX:{dx:.0f} (+{xp_gasto_dx}) \n"
                f"IQ:{iq:.0f} (+{xp_gasto_iq}) \n"
                f"HT:{ht:.0f} (+{xp_gasto_ht}) \n\n",
            )

            # MENU DE ATRIBUTOS
            opcao_menu_atributos = input(
                "Digite o número corresponde ao atributo que deseja alterar:\n"
                "[1] ST\n"
                "[2] DX\n"
                "[3] IQ\n"
                "[4] HT\n"
                "[5] Voltar\n\n"
                "Selecionar: "
            )

            # CALCULOS DAS ENTRADAS DO MENU

            # ST
            if opcao_menu_atributos == "1":
                incremento_st = input("Quantos pontos deseja gastar em ST: ")

                if incremento_st.isdigit() or incremento_st.lstrip("-").isdigit():
                    xp_gasto_st += int(incremento_st)
                    st += int(incremento_st) / 10
                else:
                    continue

            # DX
            elif opcao_menu_atributos == "2":
                incremento_dx = input("Quantos pontos deseja gastar em DX: ")

                if incremento_dx.isdigit() or incremento_dx.lstrip("-").isdigit():
                    xp_gasto_dx += int(incremento_dx)
                    dx += int(incremento_dx) / 20
                else:
                    continue

            # IQ
            elif opcao_menu_atributos == "3":
                incremento_iq = input("Quantos pontos deseja gastar em IQ: ")

                if incremento_iq.isdigit() or incremento_iq.lstrip("-").isdigit():
                    xp_gasto_iq += int(incremento_iq)
                    iq += int(incremento_iq) / 20
                else:
                    continue

            # HT
            elif opcao_menu_atributos == "4":
                incremento_ht = input("Quantos pontos deseja gastar em HT: ")

                if incremento_ht.isdigit() or incremento_ht.lstrip("-").isdigit():
                    xp_gasto_ht += int(incremento_ht)
                    ht += int(incremento_ht) / 10
                else:
                    continue

            # OPÇÃO DE VOLTAR PARA O MENU PRINCIPAL
            elif opcao_menu_atributos == "5":
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para o MENU PRINCIPAL?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_principal_criacao_personagem,
                    menu.menu_atributos_criacao_personagem,
                )

            else:
                continue

    def menu_pericias_criacao_personagem(self):

        # IMPORTS
        import os
        from menu import Menu
        from mensagens_sistema import MensagensSistema

        # VARIÁVEIS
        menu = Menu()
        validador_menu_pericias = True
        mensagem_sistema = MensagensSistema()
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
                opcao_sair = input(
                    "\n\nDeseja realmente voltar para o MENU PRINCIPAL?\n"
                    "[s]im para voltar\n"
                    "[n]ão para ficar\n\n"
                    "Selecionar: "
                )
                mensagem_sistema.deseja_voltar(
                    opcao_sair,
                    menu.menu_principal_criacao_personagem,
                    menu.menu_pericias_criacao_personagem,
                )
