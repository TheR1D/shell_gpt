FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION ignore

USER root 
RUN useradd -ms /bin/bash app

WORKDIR /home/app
COPY . /home/app/

RUN pip install --no-cache --upgrade pip \
    && pip install --no-cache /home/app \
    && mkdir -p /tmp/shell_gpt \
    && chown -R app:app /tmp/shell_gpt

USER app

VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]
