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
    offset = 0  # Rastreia a última mensagem lida para não repetir respostas
    
    print("🤖 Bot Interativo iniciado e escutando comandos no Telegram...")
    
    while True:
        try:
            # Consulta a API do Telegram por novas mensagens (timeout de 10s)
            url = f"{url_base}getUpdates?offset={offset}&timeout=10"
            resposta = requests.get(url).json()
            
            if "result" in resposta:
                for update in resposta["result"]:
                    offset = update["update_id"] + 1
                    
                    # Verifica se o pacote recebido contém uma mensagem de texto
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        texto_recebido = update["message"]["text"].strip().lower()
                        
                        # --- COMANDO 1: PREÇO (Apenas para IDs autorizados) ---
                        if texto_recebido in ["/preco", "preco"]:
                            if chat_id not in chat_ids_autorizados:
                                print(f"⚠️ Comando /preco bloqueado para ID não autorizado: {chat_id}")
                                continue
                                
                            print(f"💬 Comando /preco executado pelo ID {chat_id}.")
                            mensagem_resposta = buscar_cotacoes_atuais(config["criptos_monitoradas"])
                            
                            url_envio = f"{url_base}sendMessage"
                            payload = {"chat_id": chat_id, "text": mensagem_resposta, "parse_mode": "Markdown"}
                            requests.post(url_envio, json=payload)
                        
                        # --- COMANDO 2: AJUDA / CONVITE (Aberto para gerar o texto encaminhável) ---
                        elif texto_recebido in ["/ajuda", "ajuda", "/start", "começar"]:
                            print(f"💬 Texto de convite solicitado pelo ID: {chat_id}")
                            
                            link_bot = "https://t.me/CryptoMonitorIsmaelBot"
                            
                            # Este é o texto formatado para você encaminhar para o seu amigo
                            mensagem_resposta = (
                                "📋 *CONVITE: MONITOR CRIPTO ISMAEL*\n\n"
                                "Para começar a receber meus alertas automatizados de oscilação em tempo real "
                                "e o relatório diário das 18h, siga estes 3 passos rápidos:\n\n"
                                f"1️⃣ *Abra o Bot:* Clique no link abaixo e aperte o botão **'Iniciar'** (ou envie um 'Oi'):\n"
                                f"👉 {link_bot}\n\n"
                                "2️⃣ *Descubra seu ID:* Assim que você iniciar o bot, ele vai identificar o seu número de usuário "
                                "e mostrar na tela para você.\n\n"
                                "3️⃣ *Me mande o número:* Copie o número de ID que o bot te der e mande para mim. "
                                "Assim que eu injetar ele na nuvem, seu feed estará ativo! 🚀"
                            )
                            
                            url_envio = f"{url_base}sendMessage"
                            payload = {"chat_id": chat_id, "text": mensagem_resposta, "parse_mode": "Markdown"}
                            requests.post(url_envio, json=payload)
                            
        except Exception as e:
            print(f"❌ Erro no loop do bot: {e}")
            
        # Pausa de segurança de 1 segundo para evitar consumo excessivo de CPU
        time.sleep(1)

if __name__ == "__main__":
    escutar_telegram()