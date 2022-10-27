
FROM python:3.9

WORKDIR /code

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt

COPY producer.py ./

CMD ["python", "./producer.py"]