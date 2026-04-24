import os
import json
from playwright.sync_api import sync_playwright, Page
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, List
import base64
import time

class CookieResponse(BaseModel):
    has_banner: bool = Field(description="Verdadeiro se houver um banner de cookies pedindo aceite na tela.")
    accept_button_selector: Optional[str] = Field(description="O seletor CSS do botão de aceitar cookies, se existir.")

class LinkResponse(BaseModel):
    links: list[str] = Field(description="Lista de URLs completas ou seletores CSS dos links de anúncios de forrageiras (PDP).")

class AgenticNavigator:
    def __init__(self, headless=True):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.playwright = sync_playwright().start()
        # No Cloud Run o sandbox precisa ser desativado
        self.browser = self.playwright.chromium.launch(headless=headless, args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'])
        self.context = self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()

    def get_screenshot_bytes(self):
        """Retorna a screenshot atual da página para mandar pro Gemini"""
        return self.page.screenshot(type='jpeg', quality=80)

    def solve_cookies(self):
        """Usa Vision para detectar banner de cookies e clicar no aceite."""
        print("[Agentic Navigator] Verificando cookies...")
        time.sleep(3) # Aguarda animações
        screenshot = self.get_screenshot_bytes()
        
        # Envia a screenshot para o Gemini
        response = self.client.models.generate_content(
            model='gemini-2.5-flash', # ou gemini-2.5-flash dependendo da versão disponivel no GCP
            contents=[
                types.Part.from_bytes(data=screenshot, mime_type='image/jpeg'),
                "Analise esta página. Existe um banner de cookies pedindo permissão de aceite? Retorne os dados estruturados."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CookieResponse,
                temperature=0.1
            )
        )
        
        result = json.loads(response.text)
        if result.get("has_banner") and result.get("accept_button_selector"):
            selector = result["accept_button_selector"]
            print(f"[Agentic Navigator] Banner detectado! Tentando clicar no seletor: {selector}")
            try:
                self.page.locator(selector).first.click(timeout=3000)
                time.sleep(1) # Aguarda o banner sumir
            except Exception as e:
                print(f"[Agentic Navigator] Falha ao clicar no cookie banner: {e}")
        else:
            print("[Agentic Navigator] Nenhum banner de cookie obstrutivo detectado.")

    def find_pdp_links(self) -> List[str]:
        """Avalia a listagem atual e extrai os URLs dos produtos"""
        # Obter todos os links da tela
        links_data = self.page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            }));
        }''')
        
        # Como pode ser muita coisa, filtramos o basico do DOM e mandamos o modelo decidir
        # Ou simplesmente mandamos os links + screenshot
        links_json = json.dumps(links_data[:100]) # Limita para n estourar
        
        screenshot = self.get_screenshot_bytes()
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=screenshot, mime_type='image/jpeg'),
                f"Aqui está a imagem de uma página de listagem de máquinas agrícolas e a extração bruta de links do DOM: {links_json}. Me retorne apenas a lista das URLs que levam para a página de detalhes (PDP) das forrageiras (Veldhakselaars/Forage Harvesters)."
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=LinkResponse,
                temperature=0.1
            )
        )
        
        result = json.loads(response.text)
        return result.get("links", [])

    def extract_pdp_data(self, ForrageiraSchema, url: str):
        """Acessa um PDP e extrai dados de forma agêntica usando Structured Outputs do GenAI."""
        print(f"[Agentic Navigator] Acessando PDP: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(2)
        
        # Salvar pagina em caso de erro posterior
        self.page.screenshot(path=f"errors/last_pdp_visited.png")
        
        screenshot = self.get_screenshot_bytes()
        page_text = self.page.evaluate('() => document.body.innerText')
        
        knowledge_text = ""
        try:
            with open("knowledge_base.json", "r", encoding="utf-8") as f:
                knowledge_text = f.read()
        except:
            pass

        prompt = (
            f"Extraia os dados estruturados desta máquina agrícola. "
            f"ATENÇÃO: Em anúncios de forrageiras, quando houver 'Hours: X/Y' ou 'Horas: X/Y', o primeiro valor é Horas de Motor (motor hours) e o segundo é Horas de Rotor/Cilindro (drum hours). "
            f"Use a seguinte base de conhecimento para classificar corretamente a 'categoria' da máquina (Forrageira, Plataforma, Trator, Colheitadeira, Enfardadeira ou Outros). Se a máquina estiver listada no JSON abaixo como Forrageira ou Plataforma, use essa categoria exata. Se for claramente um trator ou colheitadeira ou enfardadeira, classifique como tal.\n"
            f"BASE DE CONHECIMENTO:\n{knowledge_text}\n\n"
            f"Se não achar algum dado, retorne null. URL atual: {url}\n\n"
            f"Texto legível da página:\n{page_text[:10000]}"
        )
        
        response = self.client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=screenshot, mime_type='image/jpeg'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ForrageiraSchema,
                temperature=0.1
            )
        )
        
        return json.loads(response.text)
        
    def navigate(self, url: str):
        self.page.goto(url, wait_until="networkidle")

    def close(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
