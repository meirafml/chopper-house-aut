import os
import gspread
from google.oauth2.service_account import Credentials
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from models.schemas import ForrageiraData

class SheetsClient:
    def __init__(self):
        # Escopos exigidos pela API do Sheets e Drive
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "storage/credentials.json")
        creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        
        if not self.spreadsheet_id:
            print("[Sheets Client] AVISO: SPREADSHEET_ID não configurado. Os dados não serão salvos na nuvem.")
            self.client = None
            return

        try:
            if creds_json:
                import json
                info = json.loads(creds_json)
                self.credentials = Credentials.from_service_account_info(info, scopes=self.scopes)
            else:
                self.credentials = Credentials.from_service_account_file(credentials_path, scopes=self.scopes)
                
            self.client = gspread.authorize(self.credentials)
            self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
            print("[Sheets Client] Conectado com sucesso à planilha.")
            self._ensure_header()
            self._load_existing_urls()
        except Exception as e:
            print(f"[Sheets Client] Erro ao conectar ao Google Sheets: {e}")
            self.client = None

    def _load_existing_urls(self):
        """Carrega as URLs já existentes na planilha para evitar duplicidade."""
        self.existing_urls = set()
        if not self.client: return
        try:
            # A URL Anúncio passa a ser a coluna 9 (I) devido à adição do Ano
            urls = self.sheet.col_values(9)
            # Ignora o cabeçalho
            self.existing_urls = set(urls[1:])
            print(f"[Sheets Client] {len(self.existing_urls)} anúncios já existentes carregados para deduplicação.")
        except Exception as e:
            print(f"[Sheets Client] Aviso ao carregar URLs existentes: {e}")

    def _ensure_header(self):
        """Garante que a planilha tenha o cabeçalho correto se estiver vazia."""
        if not self.client: return
        try:
            first_row = self.sheet.row_values(1)
            if not first_row:
                headers = ["Marca", "Modelo", "Ano de Fabricação", "Horas de Motor", "Horas de Rotor", "Tipo Plataforma", "Preço", "Localização", "URL Anúncio", "Categoria"]
                self.sheet.append_row(headers)
        except Exception as e:
            print(f"[Sheets Client] Aviso ao checar cabeçalhos: {e}")

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def save_forrageira(self, data: ForrageiraData):
        """Salva uma forrageira na planilha com retry em caso de falha de API."""
        if not self.client:
            print(f"[Sheets Client Dry Run] Dados extraídos: {data.model_dump()}")
            return
            
        if hasattr(self, 'existing_urls') and data.url_anuncio in self.existing_urls:
            print(f"[Sheets Client] Ignorando duplicado: {data.url_anuncio}")
            return
            
        allowed_categories = ["forrageira", "plataforma"]
        current_cat = data.categoria.strip().lower() if data.categoria else ""
        if current_cat and current_cat not in allowed_categories:
            print(f"[Sheets Client] Ignorando categoria não-alvo ({data.categoria}): {data.marca} {data.modelo}")
            return
            
        row = [
            data.marca,
            data.modelo,
            str(data.ano) if data.ano else "",
            str(data.horas_motor) if data.horas_motor else "",
            str(data.horas_rotor) if data.horas_rotor else "",
            data.tipo_plataforma or "",
            data.preco or "",
            data.localizacao or "",
            data.url_anuncio,
            data.categoria or ""
        ]
        
        try:
            self.sheet.append_row(row)
            self.existing_urls.add(data.url_anuncio)
            print(f"[Sheets Client] Salvo com sucesso: {data.marca} {data.modelo}")
        except Exception as e:
            print(f"[Sheets Client] Erro ao salvar row: {e}")
            raise # Relança a exceção para o Tenacity capturar e dar retry
