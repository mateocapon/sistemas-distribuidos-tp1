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
        config_params["n_duration_average"] = int(os.getenv('N_DURATION_AVERAGE', config["DEFAULT"]["N_DURATION_AVERAGE"]))
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
    n_duration_average = config_params["n_duration_average"]
    weather_filter_per_city = {}
    for i, city in enumerate(cities):
        weather_filter_per_city[city] = int(n_weather_filter_per_city[i])
    
    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level} |"
                  f"number_packet_distributor: {n_packet_distributor} | n_duration_average: {n_duration_average}")

    try:
        eof_manager = EOFManager(cities, n_packet_distributor, weather_filter_per_city, n_duration_average)
        eof_manager.run()
    except OSError as e:
        logging.error(f'action: initialize_packet_distributor | result: fail | error: {e}')

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
