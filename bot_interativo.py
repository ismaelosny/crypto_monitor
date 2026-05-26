import time
import requests
import json
import sqlite3
import yfinance as yf

# 🚨 SEU ID DO TELEGRAM (ADMINISTRADOR MASTER)
MASTER_ID = "8931413226"

def carregar_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def inicializar_banco_estados():
    """Cria uma tabela temporária para o bot lembrar o que o admin está editando."""
    conn = sqlite3.connect("historico_crypto.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estado_admin (
            chat_id TEXT PRIMARY KEY,
            status TEXT,
            ticker_selecionado TEXT,
            parametro_selecionado TEXT
        )
    """)
    conn.commit()
    conn.close()

def obter_estado(chat_id):
    conn = sqlite3.connect("historico_crypto.db")
    cursor = conn.cursor()
    cursor.execute("SELECT status, ticker_selecionado, parametro_selecionado FROM estado_admin WHERE chat_id = ?", (chat_id,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return {"status": resultado[0], "ticker": resultado[1], "parametro": resultado[2]}
    return {"status": "LIVRE", "ticker": None, "parametro": None}

def atualizar_estado(chat_id, status, ticker=None, parametro=None):
    conn = sqlite3.connect("historico_crypto.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO estado_admin (chat_id, status, ticker_selecionado, parametro_selecionado)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET 
            status=excluded.status, 
            ticker_selecionado=excluded.ticker_selecionado, 
            parametro_selecionado=excluded.parametro_selecionado
    """, (chat_id, status, ticker, parametro))
    conn.commit()
    conn.close()

def buscar_cotacoes_atuais(criptos):
    texto_resposta = "🪙 *Cotações Aktualizadas do Momento:* 🪙\n\n"
    for ticker, regras in criptos.items():
        try:
            ativo = yf.Ticker(ticker)
            preco = ativo.fast_info['last_price']
            texto_resposta += f"🔹 *{regras['nome_amigavel']}:* U$ {preco:,.2f}\n"
        except Exception as e:
            texto_resposta += f"❌ Erro ao buscar {ticker}: {e}\n"
    return texto_resposta

def escutar_telegram():
    inicializar_banco_estados()
    config = carregar_config()
    token = config["credenciais"]["telegram_token"]
    url_base = f"https://api.telegram.org/bot{token}/"
    offset = 0
    
    print("🤖 Super Bot Interativo & Gerenciador Ativo no Telegram...")
    
    while True:
        try:
            config_atualizada = carregar_config()
            chat_ids_autorizados = config_atualizada["credenciais"]["telegram_chat_ids"]
            criptos = config_atualizada["criptos_monitoradas"]
            
            url = f"{url_base}getUpdates?offset={offset}&timeout=10"
            resposta = requests.get(url).json()
            
            # CORREÇÃO DA LINHA 86: Tratamento limpo e seguro do dicionário
            if "result" in resposta:
                for update in resposta["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        texto_recebido = update["message"]["text"].strip()
                        texto_lower = texto_recebido.lower()
                        
                        # Captura o estado atual do usuário
                        estado = obter_estado(chat_id)
                        
                        # --- PROCESSADOR DE MENUS PARA O ADMINISTRADOR (MÁQUINA DE ESTADOS) ---
                        if chat_id == MASTER_ID and estado["status"] != "LIVRE":
                            
                            # Cancelar operação atual
                            if texto_lower in ["cancelar", "/cancelar", "sair"]:
                                atualizar_estado(chat_id, "LIVRE")
                                requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "❌ Operação cancelada. De volta ao modo normal."})
                                continue
                            
                            # Estado 1: Escolheu a Moeda, agora escolhe o Parâmetro
                            if estado["status"] == "AGUARDANDO_PARAMETRO":
                                listagem_tickers = list(criptos.keys())
                                try:
                                    opcao = int(texto_recebido) - 1
                                    if 0 <= opcao < len(listagem_tickers):
                                        ticker_escolhido = listagem_tickers[opcao]
                                        moeda = criptos[ticker_escolhido]
                                        
                                        msg_menu = (
                                            f"🛠️ *Configurações de {moeda['nome_amigavel']} ({ticker_escolhido}):*\n\n"
                                            f"1️⃣ Preço Piso: U$ {moeda['regra_valor']['preco_piso']:,.2f}\n"
                                            f"2️⃣ Preço Teto: U$ {moeda['regra_valor']['preco_teto']:,.2f}\n"
                                            f"3️⃣ Mayer Piso: {moeda['regra_mayer']['mayer_piso']:.2f}\n"
                                            f"4️⃣ Mayer Teto: {moeda['regra_mayer']['mayer_teto']:.2f}\n\n"
                                            "👉 *Digite o número (1 a 4) do parâmetro que deseja alterar:* "
                                        )
                                        atualizar_estado(chat_id, "AGUARDANDO_VALOR", ticker=ticker_escolhido)
                                        requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": msg_menu, "parse_mode": "Markdown"})
                                    else:
                                        requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "⚠️ Opção inválida. Digite o número da moeda listada ou 'cancelar'."})
                                except ValueError:
                                    requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "⚠️ Digite apenas o número correspondente."})
                                continue
                            
                            # Estado 2: Escolheu o parâmetro, agora vai capturar o novo valor digitado
                            if estado["status"] == "AGUARDANDO_VALOR":
                                ticker = estado["ticker"]
                                try:
                                    opcao_param = int(texto_recebido)
                                    if 1 <= opcao_param <= 4:
                                        mapeamento = {1: "preco_piso", 2: "preco_teto", 3: "mayer_piso", 4: "mayer_teto"}
                                        param_nome = mapeamento[opcao_param]
                                        
                                        atualizar_estado(chat_id, "SALVANDO_ALTERACAO", ticker=ticker, parametro=param_nome)
                                        requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": f"✍️ Digite o **novo valor numérico** para o parâmetro escolhido (use ponto para decimais):", "parse_mode": "Markdown"})
                                    else:
                                        requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "⚠️ Escolha um número de 1 a 4."})
                                except ValueError:
                                    requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "⚠️ Digite um número válido."})
                                continue

                            # Estado 3: Recebe o valor final e grava no config.json
                            if estado["status"] == "SALVANDO_ALTERACAO":
                                ticker = estado["ticker"]
                                parametro = estado["parametro"]
                                try:
                                    novo_valor = float(texto_recebido.replace(",", "."))
                                    
                                    if "preco" in parametro:
                                        config_atualizada["criptos_monitoradas"][ticker]["regra_valor"][parametro] = novo_valor
                                    else:
                                        config_atualizada["criptos_monitoradas"][ticker]["regra_mayer"][parametro] = novo_valor
                                        
                                    salvar_config(config_atualizada)
                                    atualizar_estado(chat_id, "LIVRE")
                                    
                                    msg_sucesso = f"✅ *Parâmetro Atualizado com Sucesso!*\n\nMoeda: `{ticker}`\nConfiguração `{parametro}` mudada para: `{novo_valor}`"
                                    requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": msg_sucesso, "parse_mode": "Markdown"})
                                except ValueError:
                                    requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": "⚠️ Valor inválido! Digite apenas números usando ponto para decimal (Ex: 85.50)."})
                                continue

                        # --- COMANDOS PÚBLICOS E GERAIS ---
                        
                        # 1. Comando Preço
                        if texto_lower in ["/preco", "preco"]:
                            if chat_id not in chat_ids_autorizados:
                                continue
                            mensagem_resposta = buscar_cotacoes_atuais(config_atualizada["criptos_monitoradas"])
                            requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": mensagem_resposta, "parse_mode": "Markdown"})
                        
                        # 2. Comando Ajuda / Convite
                        elif texto_lower in ["/ajuda", "ajuda", "/start", "começar"]:
                            link_bot = "https://t.me/CryptoMonitorIsmaelBot"
                            mensagem_resposta = (
                                "📋 *CONVITE: MONITOR CRIPTO ISMAEL*\n\n"
                                "Para começar a receber meus alertas automatizados de oscilação em tempo real "
                                "e o relatório diário das 18h, siga estes 3 passos rápidos:\n\n"
                                f"1️⃣ *Abra o Bot:* Clique no link abaixo e aperte o botão **'Iniciar'**:\n"
                                f"👉 {link_bot}\n\n"
                                "2️⃣ *Descubra seu ID:* Assim que você iniciar o bot, ele vai mostrar seu ID de usuário na tela.\n\n"
                                "3️⃣ *Me mande o número:* Copie o ID e passe para mim. Assim que eu ativar na nuvem, seu feed estará ligado! 🚀"
                            )
                            requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": mensagem_resposta, "parse_mode": "Markdown"})

                        # 3. Autorizar Novo ID (🔒 Exclusivo do Admin)
                        elif texto_lower.startswith("/autorizar"):
                            if chat_id != MASTER_ID:
                                continue
                            partes = texto_recebido.split()
                            if len(partes) < 2:
                                msg = "⚠️ Uso: `/autorizar ID_AQUI`"
                            else:
                                novo_id = partes[1].strip()
                                if novo_id in chat_ids_autorizados:
                                    msg = f"📭 O ID `{novo_id}` já está autorizado."
                                else:
                                    config_atualizada["credenciais"]["telegram_chat_ids"].append(novo_id)
                                    salvar_config(config_atualizada)
                                    msg = f"🚀 *Sucesso!* ID `{novo_id}` adicionado ao painel do monitor."
                            requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})

                        # 4. Painel de Controle de Regras (🔒 Exclusivo do Admin)
                        elif texto_lower in ["/painel", "painel", "configurar", "/configurar"]:
                            if chat_id != MASTER_ID:
                                continue
                            
                            texto_menu = "⚙️ *PAINEL DE CONTROLE CRIPTO*\nSelecione a moeda para editar:\n\n"
                            for idx, (ticker, dados) in enumerate(criptos.items(), start=1):
                                texto_menu += f"[{idx}] *{dados['nome_amigavel']}* ({ticker})\n"
                            
                            texto_menu += "\n👉 *Digite o número da moeda que deseja alterar:* "
                            
                            atualizar_estado(chat_id, "AGUARDANDO_PARAMETRO")
                            requests.post(f"{url_base}sendMessage", json={"chat_id": chat_id, "text": texto_menu, "parse_mode": "Markdown"})
                            
        except Exception as e:
            print(f"❌ Erro no loop do bot: {e}")
            
        time.sleep(1)

if __name__ == "__main__":
    escutar_telegram()