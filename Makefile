service=faust-project
worker=tide_test.app
partitions=8


# Build docker image
build:
	docker-compose build

run:
	docker-compose up

logs:
	docker-compose logs

# Removes old containers, free's up some space
remove:
	# Try this if this fails: docker rm -f $(docker ps -a -q)
	docker-compose rm --force -v

remove-network:
	docker network rm faust-docker-compose_default

stop:
	docker-compose stop

run-dev: build run

clean: stop remove remove-network
