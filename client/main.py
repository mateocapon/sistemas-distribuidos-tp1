#!/usr/bin/env python3

from configparser import ConfigParser
from common.client import Client
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
        config_params["server_ip"] = os.getenv('SERVER_IP', config["DEFAULT"]["SERVER_IP"])
        config_params["server_port"] = int(os.getenv('SERVER_PORT', config["DEFAULT"]["SERVER_PORT"]))
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["cities"] = os.getenv('CITIES', config["DEFAULT"]["CITIES"])
        config_params["number_readers"] = int(os.getenv('NUMBER_READERS', config["DEFAULT"]["NUMBER_READERS"]))
        config_params["chunk_size"] = int(os.getenv('CHUNK_SIZE', config["DEFAULT"]["CHUNK_SIZE"]))
        config_params["max_package_size"] = int(os.getenv('MAX_PACKAGE_SIZE', config["DEFAULT"]["MAX_PACKAGE_SIZE"]))
        config_params["n_queries"] = int(os.getenv('N_QUERIES', config["DEFAULT"]["N_QUERIES"]))
        config_params["chunk_size_trips"] = int(os.getenv('CHUNK_SIZE_TRIPS', config["DEFAULT"]["CHUNK_SIZE_TRIPS"]))
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting client".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting client".format(e))

    return config_params


def main():
    config_params = initialize_config()
    server_ip = config_params["server_ip"]
    server_port = config_params["server_port"]
    logging_level = config_params["logging_level"]
    cities = config_params["cities"]
    number_readers = config_params["number_readers"]
    max_package_size = config_params["max_package_size"]
    chunk_size = config_params["chunk_size"]
    n_queries = config_params["n_queries"]
    chunk_size_trips = config_params["chunk_size_trips"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | server_ip: {server_ip} | " 
                  f"server_port: {server_port} | logging_level: {logging_level} | "
                  f"chunk_size: {chunk_size} | max_package_size: {max_package_size} | "
                  f"number_readers: {number_readers} | cities: {cities}")

    try:
        client = Client(server_ip, server_port, number_readers, cities.split(','), 
                        chunk_size, max_package_size, n_queries, chunk_size_trips)
        client.run()
    except Exception as e:
      logging.error(f'action: run_client | result: fail | error: {str(e)}')
    except:
      logging.error(f'action: run_client | result: fail | error: unknown')

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
