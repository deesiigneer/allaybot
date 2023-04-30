FROM python:3.9-slim

WORKDIR /allaybot
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

ENV BOT_TOKEN=$BOT_TOKEN
ENV DB_HOST=$DB_HOST
ENV DB_NAME=$DB_NAME
ENV DB_PASS=$DB_PASS
ENV DB_USER=$DB_USER

COPY . .

CMD ["python", "main.py"]