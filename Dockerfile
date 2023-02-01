FROM registry.tech1a.co:81/repository/tech1a-docker-registry/python/python:3.9

COPY . /app

WORKDIR /app

RUN pip install -r requirements.txt

ENV PYTHONPATH="$PYTHONPATH:/app/src"

EXPOSE 8000

CMD uvicorn main:app --host 0.0.0.0 --port 8000
