FROM python:3-slim

ENV SHELL_INTERACTION=false
ENV OS_NAME =auto
ENV SHELL_NAME =auto

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache /app && mkdir -p /tmp/shell_gpt

VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]
