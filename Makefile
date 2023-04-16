docker-image:
	docker build -f ./server/Dockerfile -t "server:latest" .
	docker build -f ./client/Dockerfile -t "client:latest" .
	# Execute this command from time to time to clean up intermediate stages generated 
	# during client build (your hard drive will like this :) ). Don't left uncommented if you 
	# want to avoid rebuilding client image every time the docker-compose-up command 
	# is executed, even when client code has not changed
	# docker rmi `docker images --filter label=intermediateStageToBeDeleted=true -q`
.PHONY: docker-image

docker-compose-up: docker-image
	docker compose --env-file .env.dev -f docker-compose.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-down:
	docker compose --env-file .env.dev -f docker-compose.yaml stop -t 1
	docker compose --env-file .env.dev -f docker-compose.yaml down
.PHONY: docker-compose-down

docker-compose-logs:
	docker compose --env-file .env.dev -f docker-compose.yaml logs -f
.PHONY: docker-compose-logs

docker-compose-prod-up: docker-image
	docker compose --env-file .env.prod -f docker-compose.yaml up -d --build
.PHONY: docker-compose-up

docker-compose-prod-down:
	docker compose --env-file .env.prod -f docker-compose.yaml stop -t 1
	docker compose --env-file .env.prod -f docker-compose.yaml down
.PHONY: docker-compose-down

docker-compose-prod-logs:
	docker compose --env-file .env.prod -f docker-compose.yaml logs -f
.PHONY: docker-compose-logs


