# Usa a imagem oficial do Python com Debian para suportar o Chromium do Playwright
FROM python:3.11-slim

# Instalar dependências do sistema necessárias para o Playwright/Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia os requirements primeiro para otimizar o cache do Docker
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala o binário headless do Chromium para o Playwright
RUN playwright install chromium

# Copia o código do projeto
COPY . .

# Comando de execução
CMD ["python", "main.py"]
