# FROM python:3.10.12-slim
# FROM nvidia/cuda:12.2.0-cudnn8-devel-ubuntu22.04
# FROM nvidia/cuda:12.2.0-base-ubuntu22.04
FROM python:3.11

ENV PORT=5000
EXPOSE 5000

# --- start to install backend-end stuff
RUN mkdir -p /app
WORKDIR /app

# --- Install Python requirements.
# RUN apt-get update
# RUN apt-get install -y python3
# RUN apt-get install -y python3-pip

COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

# --- Copy project files
COPY ["app.py", "./"]

# --- Start server
# ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:$PORT", "app:app"]
CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout=600 --threads=10
