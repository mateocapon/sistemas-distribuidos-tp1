#!/usr/bin/env python3

from configparser import ConfigParser
from common.server import Server
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
        config_params["port"] = int(os.getenv('SERVER_PORT', config["DEFAULT"]["SERVER_PORT"]))
        config_params["listen_backlog"] = int(os.getenv('SERVER_LISTEN_BACKLOG', config["DEFAULT"]["SERVER_LISTEN_BACKLOG"]))
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["number_processes_pool"] = int(os.getenv('NUMBER_PROCESSES_POOL', config["DEFAULT"]["NUMBER_PROCESSES_POOL"]))
        config_params["n_cities"] = int(os.getenv('N_CITIES', config["DEFAULT"]["N_CITIES"]))
        config_params["max_package_size"] = int(os.getenv('MAX_PACKAGE_SIZE', config["DEFAULT"]["MAX_PACKAGE_SIZE"]))
        config_params["n_queries"] = int(os.getenv('N_QUERIES', config["DEFAULT"]["N_QUERIES"]))
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting server".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting server".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]
    port = config_params["port"]
    listen_backlog = config_params["listen_backlog"]
    number_processes_pool = config_params["number_processes_pool"]
    n_cities = config_params["n_cities"]
    n_queries = config_params["n_queries"]
    max_package_size = config_params["max_package_size"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | port: {port} | n_cities: {n_cities} | "
                  f"listen_backlog: {listen_backlog} | logging_level: {logging_level}")

    # Initialize server and start server loop
    try:
        server = Server(port, listen_backlog, number_processes_pool, n_cities, n_queries, max_package_size)
        server.run()
    except OSError as e:
        logging.error(f'action: initialize_server | result: fail | error: {e}')

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
