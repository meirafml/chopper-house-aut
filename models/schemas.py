from pydantic import BaseModel, Field
from typing import Optional

class ForrageiraData(BaseModel):
    categoria: str = Field(description="A categoria do equipamento: 'Forrageira', 'Plataforma', 'Trator', 'Colheitadeira', 'Enfardadeira' ou 'Outros'.")
    marca: str = Field(description="A marca da forrageira (Ex: Claas, John Deere, Krone, New Holland).")
    modelo: str = Field(description="O modelo exato da forrageira.")
    ano: Optional[int] = Field(None, description="O ano de fabricação da máquina. Ex: 2018, 2021.")
    horas_motor: Optional[int] = Field(None, description="Quantidade de horas de motor. Apenas os números.")
    horas_rotor: Optional[int] = Field(None, description="Quantidade de horas de rotor. Apenas os números.")
    tipo_plataforma: Optional[str] = Field(None, description="O tipo/modelo da plataforma ou header (Ex: Kemper Plus, Orbis, X-Disc).")
    preco: Optional[str] = Field(None, description="O preço com a moeda original (Ex: € 150.000,00).")
    localizacao: Optional[str] = Field(None, description="A localização da máquina (País, Estado ou Cidade).")
    url_anuncio: str = Field(description="A URL completa e canônica deste anúncio individual.")
