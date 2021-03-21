# s3_analytics_tool

## Summary

- [Requirements](#requirements)
- [Configuring credentials](#configuring-credentials)

## Requirements

We're going to install Docker and docker-compose to use this tool.

Docker (https://docs.docker.com/engine/install/)
docker-compose (https://docs.docker.com/compose/install/)

## Configuring credentials

The tool will use your local credentials (~/.aws/credentials) in case you're running locally. If you deploy this tool inside an EC2 or Fargate it will automatically use the IAM role attached to the instance.

E.g of the local credential file.

```
[default]
aws_access_key_id = xxx
aws_secret_access_key = xxx
```

## Usage

1. To build and start the container locally, run:

```shell
$ make run
```

If you want to rebuild the container, run:

```shell
$ make build
```

2. Inside the container, run:

``` shell
$ python main.py
```

This command will invoke the script. Just answer the questions and you're done!

## Testing and lint

1. To start the unit tests and the python linter, run inside the container:

```shell
$ make test
```
