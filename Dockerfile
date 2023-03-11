FROM python:3.10-slim

WORKDIR /code

COPY ./requirements.txt .

RUN pip3 install --upgrade pip \
    && pip3 install -r requirements.txt --no-cache-dir

COPY . .

ENTRYPOINT ["python3", "main.py"]
