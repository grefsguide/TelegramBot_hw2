FROM python:3.10

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
Соберите и запустите образ:

docker build -t my_telegram_bot .
docker run -d --name my_telegram_bot my_telegram_bot
