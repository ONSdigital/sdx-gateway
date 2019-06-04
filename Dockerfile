FROM onsdigital/flask-crypto-queue

ADD app /app
COPY requirements.txt /requirements.txt
COPY startup.sh /startup.sh
COPY Makefile /Makefile

RUN make build

WORKDIR app

EXPOSE 8087

ENTRYPOINT python3 -m app.main
