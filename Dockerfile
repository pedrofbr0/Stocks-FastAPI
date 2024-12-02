# Use uma imagem base do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de requisitos para o contêiner
COPY dependencies.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r dependencies.txt

# Copia o código da aplicação para o contêiner
COPY . .

# Expõe a porta em que a aplicação irá rodar
EXPOSE 8000

# Define a variável de ambiente para desativar o buffering do Python (opcional)
ENV PYTHONUNBUFFERED=1

# Comando para iniciar a aplicação usando o Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
