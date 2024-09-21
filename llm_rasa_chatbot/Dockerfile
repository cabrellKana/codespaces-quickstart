FROM python:3.10-slim
#rasa/rasa:latest-full
#python:3.10-slim
#ubuntu:22.04
#rasa/rasa:latest-full
#rasa/rasa-sdk:3.6.2

USER root

WORKDIR /app

EXPOSE 5005 5055 5432

RUN apt-get update && apt-get install -y python3 python3-pip supervisor

RUN pip install rasa-pro --extra-index-url=https://europe-west3-python.pkg.dev/rasa-releases/rasa-pro-python/simple/
RUN pip install rasa-sdk pymysql SQLAlchemy==1.4.52 html2text

RUN apt-get update && apt-get --assume-yes --no-install-recommends install build-essential curl git jq libgomp1 vim



COPY ./supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY ./dataset/init.sql /docker-entrypoint-initdb.d/init.sql

RUN chmod 775 /docker-entrypoint-initdb.d/init.sql

ADD config.yml config.yml
ADD domain.yml domain.yml
ADD credentials.yml credentials.yml
ADD endpoints.yml endpoints.yml
ADD ./nginx /etc/

CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf"]
