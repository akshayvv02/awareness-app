# Dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Specify FLASK_APP and FLASK_ENV
ENV FLASK_APP=app
ENV FLASK_ENV=production

CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
