FROM registry.tech1a.co:81/repository/tech1a-docker-registry/python/python:3.10

ENV TZ=Asia/Tehran

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app"

EXPOSE 80

WORKDIR /app/src

CMD python main.py
