FROM python:3.12.14-slim

ENV PYTHONBUFFERED=1

WORKDIR /srb

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "main"]