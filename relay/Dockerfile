FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
COPY relay/requirements.txt relay/requirements.txt
RUN pip install --no-cache-dir -r relay/requirements.txt
COPY python /app/python
RUN pip install --no-cache-dir /app/python
COPY relay /app/relay
ENV AG_ALLOWED_ORIGINS=https://aquatic-guardian.netlify.app
EXPOSE 8080
CMD ["uvicorn", "relay.app:app", "--host", "0.0.0.0", "--port", "8080"]
