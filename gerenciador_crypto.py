import json
import os

CONFIG_FILE = "config.json"

def carregar_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def menu_principal():
    while True:
        limpar_tela()
        config = carregar_config()
        criptos = config["criptos_monitoradas"]
        
        print("====== 🪙 GERENCIADOR DO MONITOR CRIPTO ======")
        print("Selecione uma moeda para editar as regras:\n")
        
        # Lista as moedas dinamicamente com base no JSON
        opcoes = list(criptos.keys())
        for i, ticker in enumerate(opcoes, start=1):
            nome = criptos[ticker]["nome_amigavel"]
            print(f" [{i}] {nome} ({ticker})")
            
        print(" [0] Sair do Gerenciador")
        print("==============================================")
        
        opcao = input("\nDigite a opção desejada: ")
        
        if opcao == "0":
            print("\nAlterações salvas. Saindo...")
            break
            
        try:
            idx = int(opcao) - 1
            if 0 <= idx < len(opcoes):
                menu_editar_moeda(opcoes[idx])
            else:
                input("\n⚠️ Opção inválida! Pressione Enter para tentar novamente.")
        except ValueError:
            input("\n⚠️ Por favor, digite um número válido. Pressione Enter.")

def menu_editar_moeda(ticker):
    while True:
        limpar_tela()
        config = carregar_config()
        moeda = config["criptos_monitoradas"][ticker]
        
        print(f"====== 🛠️ Configurações de: {moeda['nome_amigavel']} ({ticker}) ======")
        print(f" [1] Preço Piso (Nominal)  : U$ {moeda['regra_valor']['preco_piso']:,.2f} [Ativada: {moeda['regra_valor']['ativada']}]")
        print(f" [2] Preço Teto (Nominal)  : U$ {moeda['regra_valor']['preco_teto']:,.2f} [Ativada: {moeda['regra_valor']['ativada']}]")
        print(f" [3] Alternar Regra de Preço (Ligar/Desligar)")
        print(f"----------------------------------------------------------------")
        print(f" [4] Mayer Piso (Múltiplo) : {moeda['regra_mayer']['mayer_piso']:.2f} [Ativada: {moeda['regra_mayer']['ativada']}]")
        print(f" [5] Mayer Teto (Múltiplo) : {moeda['regra_mayer']['mayer_teto']:.2f} [Ativada: {moeda['regra_mayer']['ativada']}]")
        print(f" [6] Alternar Regra de Mayer (Ligar/Desligar)")
        print(f"----------------------------------------------------------------")
        print(f" [0] Voltar ao Menu Anterior")
        print("================================================================")
        
        opcao = input("\nO que deseja alterar? ")
        
        if opcao == "0":
            break
            
        if opcao == "1":
            novo_valor = input(f"Novo Preço Piso para {ticker}: U$ ")
            try:
                moeda['regra_valor']['preco_piso'] = float(novo_valor)
                salvar_config(config)
            except ValueError:
                input("⚠️ Valor inválido! Use apenas números e ponto para decimais.")
                
        elif opcao == "2":
            novo_valor = input(f"Novo Preço Teto para {ticker}: U$ ")
            try:
                moeda['regra_valor']['preco_teto'] = float(novo_valor)
                salvar_config(config)
            except ValueError:
                input("⚠️ Valor inválido!")
                
        elif opcao == "3":
            moeda['regra_valor']['ativada'] = not moeda['regra_valor']['ativada']
            salvar_config(config)
            
        elif opcao == "4":
            novo_valor = input(f"Novo Múltiplo de Mayer Piso (ex: 0.75): ")
            try:
                moeda['regra_mayer']['mayer_piso'] = float(novo_valor)
                salvar_config(config)
            except ValueError:
                input("⚠️ Valor inválido!")
                
        elif opcao == "5":
            novo_valor = input(f"Novo Múltiplo de Mayer Teto (ex: 1.40): ")
            try:
                moeda['regra_mayer']['mayer_teto'] = float(novo_valor)
                salvar_config(config)
            except ValueError:
                input("⚠️ Valor inválido!")
                
        elif opcao == "6":
            moeda['regra_mayer']['ativada'] = not moeda['regra_mayer']['ativada']
            salvar_config(config)

if __name__ == "__main__":
    menu_principal()