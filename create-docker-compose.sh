#!/bin/bash

config=$(cat ./config.txt)

eval "$config"

N_CITIES=$(echo $CITIES | tr ',' '\n' | wc -l)

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
      - $DATA_PATH:/data
      - ./client/results:/results
    networks:
      - testing_net
    depends_on:
      - server
    deploy:
      resources:
        limits:
          cpus: $CLIENT_CPU_LIMIT
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
      - CITY_TO_CALC_DISTANCE=$CITY_TO_CALC_DISTANCE
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
      - N_DISTANCES_JOIN_PARSER=$N_DISTANCES_JOIN_PARSER
      - DISTANCES_JOIN_PARSER_CITY=$CITY_TO_CALC_DISTANCE
      - N_DISTANCE_CALCULATOR=$N_DISTANCE_CALCULATOR
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


for i in $(seq 0 $((N_DISTANCES_JOIN_PARSER - 1))); do
echo "
  distances-join-parser-$i:
    container_name: distances-join-parser-$i
    image: distances-join-parser:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - CITY=$CITY_TO_CALC_DISTANCE
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
done

for i in $(seq 0 $((N_DISTANCE_CALCULATOR - 1))); do
echo "
  distance-calculator-$i:
    container_name: distance-calculator-$i
    image: distance-calculator:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - EFFICIENT=$EFFICIENT_DC
    networks:
      - testing_net
    depends_on:
      rabbitmq:
        condition: service_healthy
" >> docker-compose-dev.yaml
done

echo "
  average-distances:
    container_name: average-distances
    image: average-distances:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=INFO
      - MINIMUM_DISTANCE_KM=$MINIMUM_DISTANCE_KM
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
