#!/usr/bin/env python3

from configparser import ConfigParser
from common.eofmanager import EOFManager
import logging
import os

"""
This file is based on the tp0 main file.
"""

def initialize_config():
    """ Parse env variables or config file to find program config params

    Function that search and parse program configuration parameters in the
    program environment variables first and the in a config file. 
    If at least one of the config parameters is not found a KeyError exception 
    is thrown. If a parameter could not be parsed, a ValueError is thrown. 
    If parsing succeeded, the function returns a ConfigParser object 
    with config parameters
    """

    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["cities"] = os.getenv('CITIES', config["DEFAULT"]["CITIES"])
        config_params["number_packet_distributor"] = int(os.getenv('N_PACKET_DISTRIBUTOR', config["DEFAULT"]["N_PACKET_DISTRIBUTOR"]))
        config_params["n_weather_filter_per_city"] = os.getenv('N_WEATHER_FILTER_PER_CITY', config["DEFAULT"]["N_WEATHER_FILTER_PER_CITY"])
        config_params["n_stations_joiner_per_city"] = os.getenv('N_STATIONS_JOINER_PER_CITY', config["DEFAULT"]["N_STATIONS_JOINER_PER_CITY"])
        config_params["join_parser_city"] = os.getenv('DISTANCES_JOIN_PARSER_CITY', config["DEFAULT"]["DISTANCES_JOIN_PARSER_CITY"])
        config_params["n_duration_average"] = int(os.getenv('NUMBER_AVERAGE_DURATION_PROCESSES', config["DEFAULT"]["NUMBER_AVERAGE_DURATION_PROCESSES"]))
        config_params["n_distance_join_parser"] = int(os.getenv('N_DISTANCES_JOIN_PARSER', config["DEFAULT"]["N_DISTANCES_JOIN_PARSER"]))
        config_params["n_distance_calculator"] = int(os.getenv('N_DISTANCE_CALCULATOR', config["DEFAULT"]["N_DISTANCE_CALCULATOR"]))
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]
    n_packet_distributor = config_params["number_packet_distributor"]
    cities = config_params["cities"].split(',')
    n_weather_filter_per_city = config_params["n_weather_filter_per_city"].split(',')
    n_stations_joiner_per_city = config_params["n_stations_joiner_per_city"].split(',')
    n_duration_average = config_params["n_duration_average"]
    n_distance_join_parser = config_params["n_distance_join_parser"]
    join_parser_city = config_params["join_parser_city"]
    n_distance_calculator = config_params["n_distance_calculator"]
    weather_filter_per_city = {}
    stations_joiner_per_city = {}
    for i, city in enumerate(cities):
        weather_filter_per_city[city] = int(n_weather_filter_per_city[i])
        stations_joiner_per_city[city] = int(n_stations_joiner_per_city[i])
    
    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.info(f"action: config | result: success | logging_level: {logging_level} |"
                  f"number_packet_distributor: {n_packet_distributor} | " 
                  f"n_duration_average: {n_duration_average} | "
                  f"weather_filter_per_city: {weather_filter_per_city}")

    try:
        eof_manager = EOFManager(cities, n_packet_distributor, weather_filter_per_city,
                                 stations_joiner_per_city, n_duration_average, 
                                 n_distance_join_parser, join_parser_city, n_distance_calculator)
        eof_manager.run()
    except Exception as e:
        logging.error(f'action: run_eof_manager | result: fail | error: {str(e)}')
    except:
        logging.error(f'action: run_eof_manager | result: fail | error: unknown')

def initialize_log(logging_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging_level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == "__main__":
    main()
