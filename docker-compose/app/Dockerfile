FROM python:3.8.2

RUN pip install --upgrade pip

WORKDIR /app

ADD . /app

RUN pip install -r requirements.txt

EXPOSE 5001

ENTRYPOINT ["python"]

CMD ["app.py"]
