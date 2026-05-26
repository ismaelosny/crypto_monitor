import json
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone
import banco_cripto
import alertador_telegram

def carregar_configuracoes():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def gerar_resumo_diario(criptos, horario_atual):
    """Gera um relatório consolidado com a variação diária de todas as moedas."""
    print("📋 Preparando o resumo diário das 18h...")
    texto_resumo = f"📊 *Fechamento Diário Cripto* 📊\n🕒 _{horario_atual}_\n\n"
    
    for ticker, regras in criptos.items():
        try:
            ativo_yf = yf.Ticker(ticker)
            # Puxa os dados de hoje e de ontem
            historico = ativo_yf.history(period="2d")
            
            if len(historico) >= 2:
                preco_atual = float(historico['Close'].iloc[-1])
                preco_anterior = float(historico['Close'].iloc[-2])
                # Calcula a variação de fechamento a fechamento
                variacao_dia = ((preco_atual - preco_anterior) / preco_anterior) * 100
            else:
                # Fallback caso dê algum erro no histórico curto
                info = ativo_yf.info
                preco_atual = info.get("regularMarketPrice") or info.get("currentPrice")
                variacao_dia = info.get("regularMarketChangePercent") or 0.0

            # Define o emoji com base na variação do dia
            emoji = "🟢" if variacao_dia >= 0 else "🔴"
            sinal = "+" if variacao_dia >= 0 else ""
            
            texto_resumo += f"{emoji} *{regras['nome_amigavel']}:*\n"
            texto_resumo += f"   ↳ Preço: U$ {preco_atual:,.2f}\n"
            texto_resumo += f"   ↳ Var. 24h: {sinal}{variacao_dia:.2f}%\n\n"
            
        except Exception as e:
            texto_resumo += f"⚠️ Erro ao puxar dados de {ticker}: {e}\n\n"
            
    texto_resumo += "💡 _Novas checagens de gatilhos continuam automáticas._"
    alertador_telegram.enviar_mensagem_telegram(texto_resumo)

def rodar_ciclo_cripto(modo_resumo=False):
    config = carregar_configuracoes()
    criptos = config["criptos_monitoradas"]
    
    fuso_brasilia = timezone(timedelta(hours=-3))
    horario_atual = datetime.now(fuso_brasilia).strftime("%Y-%m-%d %H:%M:%S")

    # Se o script foi acionado pelo cron das 18h, ele envia o resumo e finaliza
    if modo_resumo:
        gerar_resumo_diario(criptos, horario_atual)
        return

    print(f"🤖 Iniciando monitoramento matemático de Cripto...")
    banco_cripto.inicializar_banco()
    
    for ticker, regras in criptos.items():
        try:
            nome = regras["nome_amigavel"]
            ativo_yf = yf.Ticker(ticker)
            historico = ativo_yf.history(period="250d")
            
            if historico.empty:
                continue
                
            preco_atual = float(historico['Close'].iloc[-1])
            media_200 = float(historico['Close'].tail(200).mean())
            multiplo_mayer = preco_atual / media_200
            
            banco_cripto.salvar_cotacao(ticker, preco_atual, multiplo_mayer, horario_atual)
            print(f"📊 [{nome}] Preço: U$ {preco_atual:.2f} | Mayer: {multiplo_mayer:.2f}")

            # [AQUI PERMANECEM EXATAMENTE AS MESMAS REGRAS DE PISO/TETO E MAYER DO PASSO ANTERIOR]
            if regras["regra_mayer"]["ativada"]:
                piso_mayer = regras["regra_mayer"]["mayer_piso"]
                teto_mayer = regras["regra_mayer"]["mayer_teto"]
                if multiplo_mayer <= piso_mayer:
                    if not banco_cripto.verificar_se_alerta_foi_enviado_recente(ticker, "MAYER_PISO"):
                        msg = f"🚨 *Múltiplo de Mayer - COMPRA EXTREMA*\n\n🪙 *{nome} ({ticker})* está muito abaixo da média histórica!\n\n🔹 *Preço Atual:* U$ {preco_atual:.2f}\n📉 *Mapeamento de Mayer:* {multiplo_mayer:.2f}\n🕒 Horário: {horario_atual}"
                        alertador_telegram.enviar_mensagem_telegram(msg)
                        banco_cripto.registrar_disparo_alerta(ticker, "MAYER_PISO", multiplo_mayer, horario_atual)
                elif multiplo_mayer >= teto_mayer:
                    if not banco_cripto.verificar_se_alerta_foi_enviado_recente(ticker, "MAYER_TETO"):
                        msg = f"⚠️ *Múltiplo de Mayer - TOPO/EUFORIA*\n\n🪙 *{nome} ({ticker})* esticou demais acima da média!\n\n🔹 *Preço Atual:* U$ {preco_atual:.2f}\n📈 *Mapeamento de Mayer:* {multiplo_mayer:.2f}\n🕒 Horário: {horario_atual}"
                        alertador_telegram.enviar_mensagem_telegram(msg)
                        banco_cripto.registrar_disparo_alerta(ticker, "MAYER_TETO", multiplo_mayer, horario_atual)

            if regras["regra_valor"]["ativada"]:
                piso_preco = regras["regra_valor"]["preco_piso"]
                teto_preco = regras["regra_valor"]["preco_teto"]
                if preco_atual <= piso_preco:
                    if not banco_cripto.verificar_se_alerta_foi_enviado_recente(ticker, "PRECO_PISO"):
                        msg = f"🛒 *Suporte Atingido: {nome}*\n\n🔹 *Preço Atual:* U$ {preco_atual:.2f}\n🔻 *Piso Configurado:* U$ {piso_preco:.2f}\n🕒 Horário: {horario_atual}"
                        alertador_telegram.enviar_mensagem_telegram(msg)
                        banco_cripto.registrar_disparo_alerta(ticker, "PRECO_PISO", preco_atual, horario_atual)
                elif preco_atual >= teto_preco:
                    if not banco_cripto.verificar_se_alerta_foi_enviado_recente(ticker, "PRECO_TETO"):
                        msg = f"📈 *Resistência Atingida: {nome}*\n\n🔹 *Preço Atual:* U$ {preco_atual:.2f}\n🔺 *Teto Configurado:* U$ {teto_preco:.2f}\n🕒 Horário: {horario_atual}"
                        alertador_telegram.enviar_mensagem_telegram(msg)
                        banco_cripto.registrar_disparo_alerta(ticker, "PRECO_TETO", preco_atual, horario_atual)

        except Exception as e:
            print(f"❌ Falha ao processar {ticker}: {e}")

if __name__ == "__main__":
    # Verifica se a palavra 'resumo' foi digitada junto ao comando
    checar_modo_resumo = len(sys.argv) > 1 and sys.argv[1] == "resumo"
    rodar_ciclo_cripto(modo_resumo=checar_modo_resumo)