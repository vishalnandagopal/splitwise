FROM python:3.12

LABEL splitwise-docker image

RUN ["pip3","install","poetry==1.7.0"]

WORKDIR /splitwise

COPY poetry.lock pyproject.toml /splitwise

RUN ["poetry","config","virtualenvs.create","false"]

RUN ["poetry","install","--no-interaction","--no-ansi"]

COPY . .

ENV PYTHONUNBUFFERED=1

CMD poetry run python3 testing.py