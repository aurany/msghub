
FROM python:3.9

WORKDIR /code

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY consumer.py ./

CMD ["python", "./consumer.py"]