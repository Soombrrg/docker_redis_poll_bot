FROM python:3.13-alpine AS poll_bot

ENV PYTHONUNBUFFERED=1

RUN apk add \
    build-base

COPY requirements.txt /temp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip pip install -r /temp/requirements.txt

COPY poll_bot /poll_bot
WORKDIR /poll_bot

RUN adduser --disabled-password botuser
USER botuser
