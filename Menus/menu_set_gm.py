class MenuSetGM:

    # Mostra o menu onde o GM escolhe os parâmetros da campanha
    def menu_set_gm():
        import os

        # CONDIÇÃO PARA COLETAR OS DADOS
        verificador_set_gm = True

        # MENU QUE SETA OS DADOS DA CAMPANHA
        while verificador_set_gm:
            os.system("cls")
            # MENSAGEM DE SAUDAÇÃO
            print(
                "\nOk. Vamos definir as informações da campanha.\n\n"
                "Digite [sair] a qualquer momento para retornar a tela inicial\n"
                "Caso erre ou deseje editar algum dado, no final haverá uma opção.\n"
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

                from iniciar_programa import inicia_programa

                voltar_para_inicio = inicia_programa()
                voltar_para_inicio.inicio_do_programa()

            # ---------------------------------------------------#

            # NÍVEL DE TECNOLOGIA DA CAMPANHA
            while verificador_tl_campanha:

                tl_campanha = input("\nNÍVEL DE TECNOLOGIA:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if tl_campanha.lower() == "sair":
                    from iniciar_programa import inicia_programa

                    voltar_para_inicio = inicia_programa()
                    voltar_para_inicio.inicio_do_programa()

                # TESTA SE O VALOR DE TL_CAMPANHA É UM NÚMERO
                elif tl_campanha.isdigit():
                    verificador_tl_campanha = False

            # ---------------------------------------------------#

            # QUANTIDADE DE PONTOS INICIAL DOS PERSONAGENS
            while verificador_pontos:

                pontos_campanha = input("\nPONTOS:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if pontos_campanha.lower() == "sair":
                    from iniciar_programa import inicia_programa

                    voltar_para_inicio = inicia_programa()
                    voltar_para_inicio.inicio_do_programa()

                # TESTA SE O VALOR DE PONTO_CAMAPANHA É UM NÚMERO
                elif pontos_campanha.isdigit():
                    verificador_pontos = False

            # ---------------------------------------------------#

            while verificador_desv:

                desvantagens_campanha = input("\nDESVANTAGENS:\n")

                # CASO DESEJE VOLTAR PARA A TELA DE INÍCIO
                if desvantagens_campanha.lower() == "sair":
                    from iniciar_programa import inicia_programa

                    voltar_para_inicio = inicia_programa()
                    voltar_para_inicio.inicio_do_programa()

                # TESTA SE O VALOR DE PONTO_CAMAPNHA É UM NÚMERO
                elif desvantagens_campanha.isdigit():
                    verificador_desv = False

            # VERIFICA SE OS DADOS QUE O GM SETOU ESTÃO CORRETOS
            while verificador_pergunta_final:

                pergunta_final = input(
                    "\n\nOs dados da campanha estão corretas?\n\n"
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
                        "Caso digite [s] sua campanha será criada.\n"
                        "Caso ainda deseje alterar algum dando digite [n]\n"
                    )

                    # CASO DESEJE PROSSEGUIR
                    if tela_seguinte.lower() == "s":
                        ...  # função da próxima tela

                    elif tela_seguinte.lower() == "n":
                        continue

                # CASO DESEJE PREENCHER NOVAMENTE
                elif pergunta_final.lower() == "n":
                    break

                # CASO DESEJE VOLTAR PARA A TELA INICIAL
                elif pergunta_final.lower() == "sair":
                    from iniciar_programa import IniciaPrograma

                    voltar_para_inicio = IniciaPrograma()
                    voltar_para_inicio.inicio_do_programa()
                else:
                    break

            os.system("cls")

    menu_set_gm()
