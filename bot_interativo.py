import time
import requests
import json
import yfinance as yf

def carregar_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def buscar_cotacoes_atuais(criptos):
    """Busca o preço rápido no Yahoo Finance para responder ao comando."""
    texto_resposta = "🪙 *Cotações Atualizadas do Momento:* 🪙\n\n"
    for ticker, regras in criptos.items():
        try:
            ativo = yf.Ticker(ticker)
            # Puxa o último preço rápido (fast info)
            preco = ativo.fast_info['last_price']
            texto_resposta += f"🔹 *{regras['nome_amigavel']}:* U$ {preco:,.2f}\n"
        except Exception as e:
            texto_resposta += f"❌ Erro ao buscar {ticker}: {e}\n"
    return texto_resposta

def escutar_telegram():
    config = carregar_config()
    token = config["credenciais"]["telegram_token"]
    chat_ids_autorizados = config["credenciais"]["telegram_chat_ids"]
    
    url_base = f"https://api.telegram.org/bot{token}/"
    offset = 0 # Rastreia qual foi a última mensagem lida para não responder repetido
    
    print("🤖 Bot Interativo iniciado e escutando comandos no Telegram...")
    
    while True:
        try:
            # Pergunta ao Telegram se há novas mensagens (timeout de 10s para manter a conexão aberta)
            url = f"{url_base}getUpdates?offset={offset}&timeout=10"
            resposta = requests.get(url).json()
            
            if "result" in resposta:
                for update in resposta["result"]:
                    offset = update["update_id"] + 1
                    
                    # Verifica se o update contém uma mensagem de texto
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        texto_recebido = update["message"]["text"].strip().lower()
                        
                        # TRAVA DE SEGURANÇA: Só responde para quem está na lista do config.json
                        if chat_id not in chat_ids_autorizados:
                            print(f"⚠️ Tentativa de comando por ID não autorizado: {chat_id}")
                            continue
                            
                        # Processa o comando
                        if texto_recebido == "/preco" or texto_recebido == "preco":
                            print(f"💬 Comando recebido de {chat_id}. Buscando preços...")
                            
                            # Busca os preços e monta o texto
                            mensagem_resposta = buscar_cotacoes_atuais(config["criptos_monitoradas"])
                            
                            # Envia a resposta de volta para o usuário
                            url_envio = f"{url_base}sendMessage"
                            payload = {
                                "chat_id": chat_id,
                                "text": mensagem_resposta,
                                "parse_mode": "Markdown"
                            }
                            requests.post(url_envio, json=payload)
                            
        except Exception as e:
            print(f"❌ Erro no loop do bot: {e}")
            
        # Pequena pausa de 1 segundo para não estressar o processador da VM
        time.sleep(1)

if __name__ == "__main__":
    escutar_telegram()