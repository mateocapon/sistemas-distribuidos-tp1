docker-image:
	docker build -f ./base-images/python-base.dockerfile -t rabbitmq-python-base:0.0.1 .
	docker build -f ./server/Dockerfile -t "server:latest" .
	docker build -f ./client/Dockerfile -t "client:latest" .
	docker build -f ./packet-distributor/Dockerfile -t "packet-distributor:latest" .
	docker build -f ./pipeline-average-time-weather/weather-filter/Dockerfile -t "weather-filter:latest" .
	docker build -f ./pipeline-average-time-weather/average-duration/Dockerfile -t "average-duration:latest" .
	docker build -f ./eof-manager/Dockerfile -t "eof-manager:latest" .
	# Execute this command from time to time to clean up intermediate stages generated 
	# during client build (your hard drive will like this :) ). Don't left uncommented if you 
	# want to avoid rebuilding client image every time the docker-compose-up command 
	# is executed, even when client code has not changed
	# docker rmi `docker images --filter label=intermediateStageToBeDeleted=true -q`
.PHONY: docker-image

docker-compose-up: docker-image
	docker compose -f docker-compose.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker compose  -f docker-compose.yaml stop -t 1
	docker compose -f docker-compose.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose -f docker-compose.yaml logs -f
.PHONY: docker-compose-logs


