# sdx-gateway

[![Build Status](https://travis-ci.org/ONSdigital/sdx-gateway.svg?branch=master)](https://travis-ci.org/ONSdigital/sdx-gateway) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/0d8f1899b0054322b9d0ec8f2bd62d86)](https://www.codacy.com/app/ons-sdc/sdx-gateway?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/sdx-gateway&amp;utm_campaign=Badge_Grade) [![codecov](https://codecov.io/gh/ONSdigital/sdx-gateway/branch/master/graph/badge.svg)](https://codecov.io/gh/ONSdigital/sdx-gateway)

The sdx-gateway app is used within the Office National of Statistics (ONS) as a gatekeeper service between SDX and EQ. It binds to an upstream RabbitMQ queue, and passes any messages to a downstream queue. Stopping this service keeps submissions on the EQ queues for the duration of the gateway's downtime, which is useful when carrying out production deployments.

## Installation

*It is recommended that this service is installed inside a virtualenv.*

To install, use:

```bash
make build
```

To run the test suite, use:

```bash
make test
```

It's also possible to build sdx-gateway within a container using docker. From the sdx-gateway directory:

    $ docker build -t sdx-gateway .

## Usage

To start sdx-gateway service locally, use the following command:

    python server.py

If you've built the image under docker, you can start using the following:

    docker run -p 5000:5000 sdx-gateway

sdx-gateway by default binds to port 5000 on localhost. It exposes a single `/healthcheck` endpoint, which will return a `200` code if the application is running, along with status of its upstream and downstream queue bindings, if any are bound.

## Configuration

Environment variables available for configuration are listed below:

| Environment Variable         | Default            | Description
|------------------------------|--------------------|----------------
| PORT                         | `5000`             | Port to listen on
| SDX_GATEWAY_DEFAULT_USER     | `rabbit            | RabbitMQ username
| SDX_GATEWAY_DEFAULT_PASSWORD | `rabbit`           | RabbitMQ password
| SDX_GATEWAY_RABBIT_HOST      | `0.0.0.0`          | Port to listen on
| SDX_RABBIT_GATEWAY_HOST2     | `0.0.0.0`          | Port to listen on
