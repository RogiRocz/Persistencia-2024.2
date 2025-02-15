# Use uma imagem base oficial do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos para o diretório de trabalho
COPY requirements-docker.txt .

# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copia o restante do código do projeto para o diretório de trabalho
COPY . .

# Copie o script db_connect.py para o container
COPY db_connect.py /app/db_connect.py

# Expõe a porta que a aplicação irá rodar
EXPOSE 8000

# Execute o script db_connect.py antes de iniciar o uvicorn
CMD ["sh", "-c", "python /app/db_connect.py && uvicorn endpoints:app --host 0.0.0.0 --port 8000"]
