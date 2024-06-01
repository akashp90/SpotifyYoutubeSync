FROM python:3.7.17-bookworm

RUN apt-get update -y && apt-get upgrade -y && apt-get install git python3-dev python3-pip python3-setuptools build-essential libssl-dev libseccomp-dev -y


ADD ./requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install gunicorn[gevent] && pip install --no-cache-dir -r ./requirements.txt

ENV FLASK_APP=SpotifyYoutubeSync
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION

ENV AWS_ACCESS_KEY_ID $AWS_ACCESS_KEY_ID
ENV AWS_SECRET_ACCESS_KEY $AWS_SECRET_ACCESS_KEY
ENV AWS_DEFAULT_REGION $AWS_DEFAULT_REGION


ADD . /SpotifyYoutubeSync

WORKDIR /SpotifyYoutubeSync



EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:5000 'run_server:gunicorn_app' --log-level info --workers=5
