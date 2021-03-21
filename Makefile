run:
	docker-compose up -d --force-recreate && docker exec -it s3_analytics /bin/bash

build:
	docker-compose build --no-cache

test:
	pylint *.py && python -m unittest
