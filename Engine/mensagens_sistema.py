class MensagensSistema:
    def deseja_voltar_parametro(self, x, y, z):
        opcao = x
        if opcao.lower() == "s":
            return y
        elif opcao.lower() == "n":
            return z
        else:
            return None

    def deseja_voltar(self, x, y, z):
        opcao = x
        if opcao.lower() == "s":
            return y()
        elif opcao.lower() == "n":
            return z()
        else:
            return None

    def deseja_prosseguir_parametro(self, x, y, z):
        opcao = x
        if opcao.lower() == "s":
            return y
        elif opcao.lower() == "n":
            return z
        else:
            return None

    def formatar_nome_para_save(self, s):
        if " " in s:
            # Dividir a string em duas partes: antes e depois do primeiro espaço
            partes = s.split(" ", 1)
            # Retornar a parte após o primeiro espaço
            return partes[1]
        else:
            # Se não houver espaço na string, retornar a string original ou outro valor apropriado
            return s
