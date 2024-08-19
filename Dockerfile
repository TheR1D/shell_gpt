# Use the Dockerfile syntax version 1.5 for enhanced features
# syntax=docker/dockerfile:1.5

# Start from a lightweight Python 3 image
FROM python:3-slim

# Set environment variables to control shell interaction and markdown formatting
# Disable shell interaction by default (not possible in docker)
ENV SHELL_INTERACTION=false

# Disable markdown prettification by default
ENV PRETTIFY_MARKDOWN=false

# Automatically detect the operating system name
ENV OS_NAME=auto

# Automatically detect the shell name
ENV SHELL_NAME=auto

# Set the DEBIAN_FRONTEND environment variable to noninteractive to suppress prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Disable automatic clean-up of apt cache to retain downloaded packages
RUN rm /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# Update package lists and install the gcc compiler while caching the apt data
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y gcc

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the /app directory in the container
COPY . .

# Install Python dependencies using pip while caching the pip data
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install /app

# Define a mount point for temporary files
VOLUME /tmp/shell_gpt

# Set the default command to run when the container starts
ENTRYPOINT ["sgpt"]
