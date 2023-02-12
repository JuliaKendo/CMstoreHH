# pull official base image
FROM python:3.9.5-slim-buster

# custom label for the docker image
LABEL version="0.1" maintainer="CMstoreHH"

# set work directory
WORKDIR /usr/src/app

# copy project
COPY . /usr/src/app/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# start service
CMD ["python", "main.py"]
