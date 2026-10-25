FROM python:3.13.6-slim

ENV TZ=Asia/Tehran

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app"

EXPOSE 80

WORKDIR /app/src

CMD python main.py
