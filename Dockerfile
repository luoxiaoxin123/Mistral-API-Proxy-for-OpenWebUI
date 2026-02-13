FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask requests python-dotenv

COPY python.py /app/python.py

EXPOSE 6432

CMD ["python", "python.py"]
