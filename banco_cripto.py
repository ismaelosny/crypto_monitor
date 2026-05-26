import sqlite3

DB_NAME = "historico_crypto.db"

def inicializar_banco():
    """Cria as tabelas necessárias para o monitoramento de criptomoedas."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela 1: Histórico de preços em tempo real
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NOT NULL,
            preco REAL NOT NULL,
            múltiplo_mayer REAL,
            data_hora TEXT NOT NULL
        )
    """)
    
    # Tabela 2: Registro de alertas disparados (Trava Anti-Spam)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registro_alertas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT NOT NULL,
            tipo_alerta TEXT NOT NULL, -- PISO, TETO, MAYER
            valor_disparado REAL NOT NULL,
            data_hora TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def salvar_cotacao(ativo, preco, multiplo_mayer, data_hora):
    """Salva a checagem atual no banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historico_precos (ativo, preco, múltiplo_mayer, data_hora)
        VALUES (?, ?, ?, ?)
    """, (ativo, preco, multiplo_mayer, data_hora))
    conn.commit()
    conn.close()

def verificar_se_alerta_foi_enviado_recente(ativo, tipo_alerta, horas=12):
    """
    Retorna True se um alerta idêntico foi enviado nas últimas X horas.
    Cripto oscila muito, então 12 horas é um bom padrão para não inundar o Telegram.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM registro_alertas 
        WHERE ativo = ? AND tipo_alerta = ? 
        AND data_hora >= datetime('now', 'localtime', ?)
    """, (ativo, tipo_alerta, f'-{horas} hours'))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

def registrar_disparo_alerta(ativo, tipo_alerta, valor_disparado, data_hora):
    """Grava o disparo do gatilho no banco para ativar o filtro anti-spam."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO registro_alertas (ativo, tipo_alerta, valor_disparado, data_hora)
        VALUES (?, ?, ?, ?)
    """, (ativo, tipo_alerta, valor_disparado, data_hora))
    conn.commit()
    conn.close()