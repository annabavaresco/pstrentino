FROM python:3.8.2

RUN pip install --upgrade pip

WORKDIR /api

ADD . /api

RUN pip install -r requirements.txt

RUN python linear_models.py

EXPOSE 5000

ENTRYPOINT [ "python" ]

CMD ["api.py"]