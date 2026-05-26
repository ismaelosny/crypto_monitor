# 🪙 Crypto & Mayer Multiple Telegram Monitor

Uma infraestrutura de dados automatizada e pronta para a nuvem construída em Python para monitorar preços de criptomoedas (Bitcoin, Ethereum, Solana) e avaliar pontos de entrada/saída sistêmicos usando o modelo financeiro do **Múltiplo de Mayer**. O sistema salva os dados históricos localmente e dispara alertas inteligentes e relatórios diários para canais do Telegram.

---

## 🧠 Visão Geral da Arquitetura e Lógica Financeira

### 1. A Métrica do Múltiplo de Mayer
O **Múltiplo de Mayer** é uma ferramenta estatística utilizada para identificar condições de sobrecompra ou sobrevenda no mercado de cripto, medindo o desvio do preço atual em relação à sua média histórica de longo prazo.

A fórmula matemática é definida como:

$$\text{Múltiplo de Mayer} = \frac{\text{Preço Atual}}{\text{Média Móvel Simples de 200 dias (SMA 200)}}$$

- **Zona de Desconto (<= 0.75):** Historicamente representa forte desvalorização e fases de acumulação com excelente relação risco-retorno.
- **Zona Neutra (1.0):** O ativo está sendo negociado exatamente na sua média histórica de 200 dias.
- **Zona de Euforia (>= 1.40):** Representa um esticamento histórico acima da média, sinalizando topos de mercado e risco de correção.

### 2. Pipeline Operacional
1. **Ingestão de Dados:** Um agendador (`cron`) dispara o `monitor_crypto.py` a cada 15 minutes. Ele usa a biblioteca `yfinance` para buscar os últimos 250 dias de negociação para calcular a Média Móvel com precisão.
2. **Processamento Matemático:** Calcula o preço em tempo real e o Múltiplo de Mayer atual usando `pandas`.
3. **Mecanismo de Armazenamento:** Grava os logs de cotação e métricas em um banco de dados local `sqlite3` (`historico_crypto.db`).
4. **Avaliador de Regras:** Compara as métricas atuais com os limites personalizados configurados no `config.json`.
5. **Filtro Anti-Spam:** Consulta a tabela `registro_alertas` para garantir que alertas idênticos sejam travados (ex: máximo de 1 alerta a cada 12 horas) para evitar notificações em massa.
6. **Gateway de Notificação:** Envia os alertas formatados em Markdown para todos os Chat IDs cadastrados na API do Telegram.
7. **Resumo Diário Executivo:** Um gatilho independente roda às 18:00 passando o argumento `resumo` para gerar um relatório consolidado de performance do dia.

---

## 📂 Estrutura do Projeto

```text
crypto_monitor/
│
├── venv/                      # Ambiente virtual isolado (ignorado pelo Git)
├── config.json                # Credenciais de API, Chat IDs e parâmetros de gatilhos (ignorado pelo Git)
├── historico_crypto.db        # Arquivo binário do banco SQLite3 (ignorado pelo Git)
│
├── alertador_telegram.py      # Módulo HTTP para envio multicasting de mensagens via Telegram
├── banco_cripto.py            # Camada de acesso ao SQLite3, tabelas e travas anti-spam
├── monitor_crypto.py          # Core de execução: consome o mercado, processa matemática e avalia regras
└── gerenciador_crypto.py      # Interface interativa CLI via terminal para alterar o config.json de forma segura