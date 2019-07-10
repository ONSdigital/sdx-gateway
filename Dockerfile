FROM onsdigital/flask-crypto-queue

ADD app /app
COPY requirements.txt /requirements.txt
COPY startup.sh /startup.sh
COPY Makefile /Makefile

RUN make build

WORKDIR app

EXPOSE 8087

HEALTHCHECK --interval=1m30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8087/healthcheck || exit 1

ENTRYPOINT python3 -m app.main
