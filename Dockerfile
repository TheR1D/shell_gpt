FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION ignore
WORKDIR /app
COPY . /app

RUN pip install --no-cache --upgrade pip \
 && pip install --no-cache /app \
 && addgroup --system app && adduser --system --group app \
 && mkdir -p /home/app/.config/shell-gpt \
             /tmp/shell_gpt\
 && echo "api_key.txt should be here" > /home/app/.config/shell-gpt/readme.txt \
 && chown -R app:app /home/app \
                     /tmp/shell_gpt

USER app

VOLUME /home/app/.config/shell-gpt
VOLUME /tmp/shell_gpt

ENTRYPOINT ["sgpt"]

