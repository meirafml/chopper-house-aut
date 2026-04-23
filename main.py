import os
import json
from dotenv import load_dotenv
from browser.agentic_navigator import AgenticNavigator
from storage.sheets_client import SheetsClient
from models.schemas import ForrageiraData

def load_targets():
    """Lê as URLs alvos a partir da variável TARGET_SITES no .env"""
    target_sites = os.getenv("TARGET_SITES")
    if not target_sites:
        # Fallback para nossa descoberta inicial
        return ["https://www.twentrac.nl/nl/gebruikte-machine"] 
    
    return [url.strip() for url in target_sites.split(",")]

def main():
    print("Iniciando Agente de Captura de Forrageiras...")
    load_dotenv()
    
    # Validações iniciais
    if not os.getenv("GEMINI_API_KEY"):
        print("ERRO: GEMINI_API_KEY não definida no arquivo .env!")
        return

    sheets_client = SheetsClient()
    targets = load_targets()
    
    print(f"Total de sites alvos: {len(targets)}")
    
    navigator = None
    try:
        # Instancia o navegador. headless=False se quiser ver a tela rodando local.
        # No Cloud Run o ideal é headless=True (padrão)
        navigator = AgenticNavigator(headless=True)
        
        for url in targets:
            print(f"\\n--- Analisando o site: {url} ---")
            try:
                # 1. Navegar até a URL
                navigator.navigate(url)
                
                # 2. Avaliar se há banners de cookies e clicar (Visão Agentica)
                navigator.solve_cookies()
                
                # 3. Listar as URLs dos PDPs (Visão Agentica)
                # Como a listagem pode ter paginação, focaremos apenas na primeira pagina para prova de conceito.
                print("Procurando links de produtos na listagem...")
                pdp_links = navigator.find_pdp_links()
                
                if not pdp_links:
                    print("Nenhum PDP de forrageira encontrado nesta página.")
                    continue
                
                print(f"Encontrados {len(pdp_links)} anúncios potenciais. Iniciando extração...")
                
                # 4. Entrar em cada anúncio e extrair dados
                for pdp_url in pdp_links:
                    try:
                        # Extrai o dicionário validado
                        extracted_dict = navigator.extract_pdp_data(ForrageiraData, pdp_url)
                        
                        # Converte e valida via Pydantic
                        forrageira = ForrageiraData(**extracted_dict)
                        forrageira.url_anuncio = pdp_url # Força a url correta
                        
                        # Salva
                        sheets_client.save_forrageira(forrageira)
                    except Exception as e:
                        print(f"Falha ao extrair dados de {pdp_url}: {e}")
                        
            except Exception as e:
                print(f"Falha geral ao processar o site {url}: {e}")
                
    except Exception as e:
        print(f"Erro crítico no motor de navegação: {e}")
    finally:
        if navigator:
            navigator.close()
        print("\\nExecução Finalizada.")

if __name__ == "__main__":
    main()
