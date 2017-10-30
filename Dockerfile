FROM onsdigital/flask-crypto-queue

COPY app /app
COPY requirements.txt /requirements.txt
COPY startup.sh /startup.sh
COPY Makefile /Makefile

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -yq git gcc make build-essential python3-dev python3-reportlab
RUN make build

ENTRYPOINT ./startup.sh
