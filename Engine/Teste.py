from mensagens_sistema import MensagensSistema
from banco_de_dados import BancoDeDadosCampanha
from banco_de_dados import BancoDeDadosPersonagem
from menu import Menu

menu = Menu()
banco_de_dados_personagem = BancoDeDadosPersonagem()
banco_de_dados_campanha = BancoDeDadosCampanha()

menu.menu_set_player()
