FROM alpine:3.5

RUN apk add --no-cache python3 && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    rm -r /root/.cache

RUN apt-get update -y
RUN apt-get upgrade -y

RUN mkdir -p /app/logs

COPY app /app
COPY startup.sh /startup.sh
COPY requirements.txt /requirements.txt
COPY Makefile /Makefile

RUN make build

ENTRYPOINT ./startup.sh