class MensagensSistema:
    def deseja_voltar(self, x, y, z):
        opcao = x
        if opcao.lower() == "s":
            return y()
        elif opcao.lower() == "n":
            return z()
        else:
            return None

    def deseja_prosseguir(self, x, y, z):
        opcao = x
        if opcao.lower() == "s":
            return y()
        elif opcao.lower() == "n":
            return z()
        else:
            return None
