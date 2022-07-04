# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.10.5-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . ./
# COPY ./commands/ /app/commands
# COPY ./algorithms/ /app/algorithms

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["python", "poll_bot.py"]