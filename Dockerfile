
FROM python:3.9


WORKDIR /app


COPY README.md .
COPY app.py .
COPY requirements.txt .
COPY music.db .
COPY templates/ templates/


RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 5000


CMD ["python3", "-m", "flask", "run"]
