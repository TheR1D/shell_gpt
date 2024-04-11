FROM python:3-slim

ENV IN_CONTAINER=true
ENV OS_OUTSIDE_CONTAINER="Linux/Red Hat Enterprise Linux 8.8 (Ootpa)"
ENV SHELL_OUTSIDE_CONTAINER=/bin/bash

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y gcc
RUN pip install --no-cache /app && mkdir -p /tmp/shell_gpt

VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]
