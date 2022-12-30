FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m venv venv
RUN ./venv/bin/pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["./venv/bin/gunicorn", "app.web:app", "-b", "0.0.0.0", "-w", "4"]