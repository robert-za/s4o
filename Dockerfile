FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends

ENV PYTHONPATH="/s4o/"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /s4o/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app
COPY tests/ ./tests
COPY .env/ ./

EXPOSE 8000