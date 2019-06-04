## Unreleased
- Remove python 3.4 and 3.5 from travis builds
- Add python 3.7 to travis builds
- Upgrade sdc-rabbit, tornado and pika packages
- Remove multiple unused packages
- Exposing port 8087 for docker
- Updated the dockerfile to remove apt-get

## 1.3.0 2018-06-27
- Move SDX queues from EQ cluster to AWS corp

## 1.2.0 2018-01-17
- Add heartbeat interval to rabbit mq url

## 1.1.0 2017-12-15
- Upgrade rabbit library
- Raise RetryableError during process if an exception occurs

## 1.0.1 2017-11-27
- Added logging to gateway

## 1.0.0 2017-11-21
- Initial release
