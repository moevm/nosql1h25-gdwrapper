FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["sh", "-c", "python backend/manage.py migrate && python backend/manage.py runserver 0.0.0.0:8000"]
