FROM python:alpine

MAINTAINER Tobias Schneider, github@cynt4k.de

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apk add --no-cache gcc libxml2 libxml2-dev musl-dev libxslt-dev

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

WORKDIR /usr/src/app/src

ENTRYPOINT [ "python", "-u", "./enroll.py"]
