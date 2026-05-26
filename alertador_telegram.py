import requests
import json

def carregar_credenciais():
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["credenciais"]["telegram_token"], config["credenciais"]["telegram_chat_ids"]

def enviar_mensagem_telegram(texto):
    token, chat_ids = carregar_credenciais()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    for chat_id in chat_ids:
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "Markdown"
        }
        try:
            resposta = requests.post(url, json=payload)
            
            print(f"🔍 Status Code do Telegram: {resposta.status_code}")
            print(f"🔍 Resposta do Servidor: {resposta.text}")

            if resposta.status_code == 200:
                print(f"🚀 Alerta enviado com sucesso para o ID: {chat_id}")
            else:
                print(f"❌ Erro no ID {chat_id}")
        except Exception as e:
            print(f"❌ Falha ao processar o envio para o ID {chat_id}: {e}")

if __name__ == "__main__":
    enviar_mensagem_telegram("🤖 *Teste do Bot Cripto:* Janela de checagem ativa!")