FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# HF Spaces requires writable dirs under /app + uses port 7860
RUN mkdir -p /app/data /app/curriculum /app/chroma_db && \
    chmod -R 777 /app/data /app/curriculum /app/chroma_db

ENV ENV=prod
ENV PORT=7860
EXPOSE 7860

CMD ["python", "main.py"]
