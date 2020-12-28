FROM python:3.8-alpine
LABEL maintainer="vla@mst-company.ru"
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --no-cache-dir
COPY . .
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
STOPSIGNAL SIGINT
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:api"]
