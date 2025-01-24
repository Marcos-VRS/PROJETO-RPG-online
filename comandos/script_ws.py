import websocket

# URL do WebSocket (substitua pelo seu endpoint)
ws_url = "ws://127.0.0.1:8000/ws/chat/4/"


# Conectar ao WebSocket
def on_message(ws, message):
    print(f"Mensagem recebida: {message}")


def on_error(ws, error):
    print(f"Erro: {error}")


def on_close(ws, close_status_code, close_msg):
    print("Conexão fechada")


def on_open(ws):
    print("Conexão estabelecida")
    # Enviar uma mensagem de teste
    ws.send("Olá, WebSocket!")


# Configurar a conexão
websocket.enableTrace(True)
ws = websocket.WebSocketApp(
    ws_url, on_message=on_message, on_error=on_error, on_close=on_close
)
ws.on_open = on_open

# Iniciar a conexão
ws.run_forever()
