class MensagensSistema:
    def deseja_voltar():
        escolha = input(
            "Tem certeza que deseja voltar?\n" "[s] Para SAIR.\n" "[n] Para NÃO SAIR"
        ).lower()
        if escolha == "s":
            return

    def deseja_sair(): ...
    def mensagem_resposta_invalida(): ...
