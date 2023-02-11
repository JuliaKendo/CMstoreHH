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
ENV TG_TOKEN 5616918905:AAHTVnr74agAh6h4FQssXiK8tWzthtqEOxs
ENV GOOGLE_SPREADSHEET_ID 16K5VcGkoPiR-rUi40zEq1y5UeUByvmle0a7VG_WGXV8
ENV GOOGLE_RANGE_NAME Лист1!A1:B999
ENV SELENIUM_SERVER 95.31.50.174:6676
ENV REDIS_SERVER 95.31.50.174:6674
ENV HH_EMAIL cm4777777@mail.ru
ENV HH_PASSWORD Arev1991
ENV HH_CLIENT_ID G7M0ICKJO4PJL2S8L0MURJVIQ46PQP3OKPT7J3NF87FSLAH74G0TDPA383K5899F
ENV HH_CLIENT_SECRET IAHNG1NR3KSI7HI0V7KK0OSEEAQSRS8AEMPU1QNF2IBLPD91U1OP2K23FUFEOL3B
ENV ROLLBAR_TOKEN 12897dd65ce44b849f2980498bd54dd5

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# start service
CMD ["python", "main.py"]
