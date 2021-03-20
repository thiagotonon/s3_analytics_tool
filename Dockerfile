FROM python:3.8

ADD requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN useradd -ms /bin/bash docker

USER docker
WORKDIR /home/docker/s3_analytics_tool
