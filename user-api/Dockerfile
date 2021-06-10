FROM python:3.8

COPY ./api ./requirements.txt /api/

WORKDIR /api

RUN pip install uvicorn \
    && pip install -r requirements.txt

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--reload"]
