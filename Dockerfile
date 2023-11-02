# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Environment variables
ENV OXYGEN_HOST="https://hvac-simulator-a23-y2kpq.ondigitalocean.app"
ENV OXYGEN_TOKEN="QWNTDxtJzo"

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install pip requirements and clean up in a single RUN command
RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends gcc libc-dev && \
    python -m pip install -r requirements.txt && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/* && \
    adduser -u 5678 --disabled-password --gecos "" appuser && \
    chown -R appuser /app

USER appuser

WORKDIR /app
COPY . /app

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "src/main.py"]
