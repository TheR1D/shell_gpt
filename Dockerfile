# Use Python 3 Slim as base image
FROM python:3-slim AS shell_gpt

# Create unprivileged user,
# change to the new user 
# and set docker workdir to user $HOME
RUN adduser --system --group app
USER app
WORKDIR /home/app

# Copy all files into the container
COPY . /home/app

# Set up Environment parameters
# These are overriden if any of the variables are
# set using '-e' when running the container
ENV PATH="$PATH:$HOME/.local/bin:$HOME/bin" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_ROOT_USER_ACTION=ignore \
    OPENAI_API_KEY="your-OpenAI-API-key-here" \
    OPENAI_API_HOST="https://api.openai.com" \
    CHAT_CACHE_LENGTH=100 \
    CHAT_CACHE_PATH="/tmp/shell_gpt/chat_cache" \
    CACHE_LENGTH=100 \
    CACHE_PATH="/tmp/shell_gpt/cache" \
    REQUEST_TIMEOUT=60

# Upgrade PIP and install Shell GPT via PIP
RUN export PATH="$PATH:$HOME/.local/bin:$HOME/bin"; \
    /usr/local/bin/pip install pip --no-cache --upgrade; \
    /usr/local/bin/pip install --no-cache shell-gpt

# Expose shell_gpt data volume
VOLUME /tmp/shell_gpt

# Specify shell_gpt binary as entrypoint
ENTRYPOINT ["/home/app/.local/bin/sgpt"]
