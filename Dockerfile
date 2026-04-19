FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY start_server.sh .

RUN chmod +x start_server.sh

EXPOSE 7777

CMD ["./start_server.sh"]