FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION ignore
WORKDIR /app
COPY . /app

RUN pip install --no-cache --upgrade pip \
 && pip install --no-cache /app \
 && addgroup --system app && adduser --system --group app \
 && mkdir -p /tmp/shell_gpt \
 && chown -R app:app /tmp/shell_gpt

USER app

VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]

