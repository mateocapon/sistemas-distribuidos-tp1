#!/usr/bin/env python3

from configparser import ConfigParser
from common.distances_join_parser import DistancesJoinParser
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
        config_params["city"] = os.getenv('CITY', config["DEFAULT"]["CITY"])
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]    
    city = config_params["city"]    
    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level}")

    try:
        join_parser = DistancesJoinParser(city)
        join_parser.run()
    except Exception as e:
        logging.error(f'action: initialize_distances_join_parser | result: fail | error: {str(e)}')
    except:
        logging.error(f'action: initialize_distances_join_parser | result: fail | error: unknown')

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
