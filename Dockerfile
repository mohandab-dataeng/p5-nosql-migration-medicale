# Dockerfile pour le projet 5 de migration de données médicale vers mongodb

FROM python:3.12 
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
CMD ["python3", "src/script_migration.py"]
