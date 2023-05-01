#!/bin/bash

CITIES="montreal,toronto"
# el primer numero es la cantidad para la primera ciudad, el segundo para la segunda,etc.
N_WEATHER_FILTER="2,1"
N_STATIONS_JOINER="1,1"

N_PACKET_DISTRIBUTOR=2
N_CITIES=$(echo $CITIES | tr ',' '\n' | wc -l)

FIRST_YEAR_COMPARE=2016
SECOND_YEAR_COMPARE=2017
PRECTOT_COND=4

NUMBER_AVERAGE_DURATION_PROCESSES=2



echo "version: '3.9'
name: tp1
services:
  rabbitmq:
    build:
      context: ./rabbitmq
      dockerfile: rabbitmq.dockerfile
    ports:
      - 15672:15672
    networks:
      - testing_net
    healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:15672"]
        interval: 10s
        timeout: 5s
        retries: 10
" > docker-compose-dev.yaml


echo "
  client:
    container_name: client
    image: client:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
      - CITIES=$CITIES
    volumes:
      - ./client/config.ini:/config.ini
      - ./.data/dev:/data
    networks:
      - testing_net
    depends_on:
      - server
" >> docker-compose-dev.yaml


echo "  
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - N_CITIES=$N_CITIES
    volumes:
      - ./server/config.ini:/config.ini
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml


for i in $(seq 1 $N_PACKET_DISTRIBUTOR); do
echo "
  packet_distributor$i:
    container_name: packet-distributor$i
    image: packet-distributor:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - FIRST_YEAR_COMPARE=$FIRST_YEAR_COMPARE
      - SECOND_YEAR_COMPARE=$SECOND_YEAR_COMPARE
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
done

for city in $(echo $CITIES | tr ',' '\n'); do
    index=$(echo $CITIES | tr ',' '\n' | grep -n "^$city$" | cut -f1 -d:)
    n_weather_filter=$(echo $N_WEATHER_FILTER | cut -d',' -f$index)
    for j in $(seq 1 $n_weather_filter); do 
echo "
  weather-filter-$city$j:
    container_name: weather-filter-$city$j
    image: weather-filter:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - CITY=$city
      - NUMBER_AVERAGE_DURATION_PROCESSES=$NUMBER_AVERAGE_DURATION_PROCESSES
      - PRECTOT_COND=$PRECTOT_COND
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
    done
done

for i in $(seq 0 $((NUMBER_AVERAGE_DURATION_PROCESSES - 1))); do
echo "
  average-duration-$i:
    container_name: average-duration-$i
    image: average-duration:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - PROCESS_ID=$i
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
done

echo "
  results-collector-average:
    container_name: results-collector-average
    image: results-collector-average:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - NUMBER_AVERAGE_DURATION_PROCESSES=$NUMBER_AVERAGE_DURATION_PROCESSES
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml

echo "
  eof-manager:
    container_name: eof-manager
    image: eof-manager:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - N_PACKET_DISTRIBUTOR=$N_PACKET_DISTRIBUTOR
      - CITIES=$CITIES
      - N_WEATHER_FILTER_PER_CITY=$N_WEATHER_FILTER
      - N_STATIONS_JOINER_PER_CITY=$N_STATIONS_JOINER
      - NUMBER_AVERAGE_DURATION_PROCESSES=$NUMBER_AVERAGE_DURATION_PROCESSES
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml


for city in $(echo $CITIES | tr ',' '\n'); do
    index=$(echo $CITIES | tr ',' '\n' | grep -n "^$city$" | cut -f1 -d:)
    n_stations_joiner=$(echo $N_STATIONS_JOINER | cut -d',' -f$index)
    for j in $(seq 1 $n_stations_joiner); do 
echo "
  stations-joiner-$city$j:
    container_name: stations-joiner-$city$j
    image: stations-joiner:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - CITY=$city
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
    done
done

for city in $(echo $CITIES | tr ',' '\n'); do
echo "
  trips-per-year-$city:
    container_name: trips-per-year-$city
    image: trips-per-year:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - CITY=$city
      - FIRST_YEAR_COMPARE=$FIRST_YEAR_COMPARE
      - SECOND_YEAR_COMPARE=$SECOND_YEAR_COMPARE
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
done

echo "
  results-collector-trips-per-year:
    container_name: results-collector-trips-per-year
    image: results-collector-trips-per-year:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - N_CITIES=$N_CITIES
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml

echo "
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
" >> docker-compose-dev.yaml
