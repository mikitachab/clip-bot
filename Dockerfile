FROM python:3.8

RUN apt-get update && apt-get install -y ffmpeg
RUN python3.8 -m pip install --upgrade youtube_dl

COPY . /bot
WORKDIR /bot

RUN python3.8 -m pip install -r requirements.txt
