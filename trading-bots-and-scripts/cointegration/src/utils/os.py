# -*- encoding: utf-8 -*-
# src/utils/os.py
# author: steinkirch
# Utils methods.

import os
import sys
import json
import copy
import logging
import datetime
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pprint import PrettyPrinter


def save_json(destination: str, data: dict) -> None:
    """Save JSON data to a destination in disk."""

    try:
        with open(destination, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, indent=4)

    except (IOError, TypeError) as e:
        print(f'Could not save {destination}: {e}')

def open_json(filepath: str) -> dict:
    """Load and parse a JSON file."""

    try:
        with open(filepath, 'r', encoding='utf-8') as infile:
            return json.load(infile)

    except (IOError, FileNotFoundError, TypeError) as e:
        print(f'Failed to parse: "{filepath}": {e}')


def save_csv(df: pd.DataFrame, destination: str) -> None:
    """Save CSV data to a destination in disk."""
    
    df.to_csv(destination, index=False)


def open_csv(filepath: str) -> None:
    """Load and parse a CSV file."""
    
    return pd.read_csv(filepath)


def create_dir(result_dir: str) -> None:
    """Check whether a directory exists and create it if needed."""

    try:
        if not os.path.isdir(result_dir):
            os.mkdir(result_dir)

    except OSError as e:
        print(f'Could not create {result_dir}: {e}')


def deep_copy(dict_to_clone: dict) -> dict:
    """Deep copy (not reference copy) to a dict."""

    return copy.deepcopy(dict_to_clone)


def file_exists(dir_path: str, filename: str) -> bool:
    """Check if a file exists in a directory."""

    return os.path.isfile(format_path(dir_path, filename))


def exit_with_error(message: str) -> None:
    """Log an error message and halt the program."""

    log_error(message)
    sys.exit(1)


def format_path(dir_path: str, filename: str) -> str:
    """Format a OS full filepath."""

    return os.path.join(dir_path, filename)


def pprint(data: dict, indent=None) -> None:
    """Print dicts and data in a suitable format"""

    print()
    indent = indent or 4
    pp = PrettyPrinter(indent=indent)
    pp.pprint(data)
    print()


def get_datetime() -> str:
    """Get the current datetime."""

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_error(string: str) -> None:
    """Print STDOUT error using the logging library."""

    logging.error('🚨 %s', string)


def log_info(string: str) -> None:
    """Print STDOUT info using the logging library."""

    logging.info('ℹ️ %s', string)


def log_debug(string: str) -> None:
    """Print STDOUT debug using the logging library."""

    logging.debug('🟨 %s', string)


def set_logging(log_level: str) -> None:
    """Set logging level according to .env config."""

    if log_level.lower() == 'info':
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    elif log_level.lower() == 'error':
        logging.basicConfig(level=logging.ERROR, format='%(message)s')

    elif log_level.lower() == 'debug':
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    else:
        print(f'Logging level {log_level} is not available. Setting to ERROR')
        logging.basicConfig(level=logging.ERROR, format='%(message)s')


def load_config() -> dict:
    """Load and set environment variables."""

    env_file = Path('.') / '.env'
    if not os.path.isfile(env_file):
        print('Please create an .env file')
        sys.exit(1)

    env_vars = {}
    load_dotenv(env_file)

    try:
        env_vars['PRICE_HISTORY_FILE'] = os.getenv("PRICE_HISTORY_FILE")
        env_vars['COINTEGRATION_FILE'] = os.getenv("COINTEGRATION_FILE")
        env_vars['ZSCORE_FILE'] = os.getenv("ZSCORE_FILE")
        env_vars['BACKTEST_FILE'] = os.getenv("BACKTEST_FILE")
        env_vars['OUTPUTDIR'] = os.getenv("OUTPUTDIR")

        env_vars['CEX'] = os.getenv("CEX")
        env_vars['API_KEY'] = os.getenv("API_KEY")
        env_vars['API_SECRET'] = os.getenv("API_SECRET")

        env_vars['BYBIT_URL'] = os.getenv("BYBIT_URL")
        env_vars['TIMEFRAME'] = os.getenv("TIMEFRAME")
        env_vars['PLIMIT'] = os.getenv("PLIMIT")
        env_vars['TOKEN1'] = os.getenv("TOKEN1")
        env_vars['TOKEN2'] = os.getenv("TOKEN2")
        env_vars['KLINE_LIMIT'] = os.getenv("KLINE_LIMIT")   
        env_vars['ZSCORE_WINDOW'] = os.getenv("ZSCORE_WINDOW")       

        set_logging(os.getenv("LOG_LEVEL"))

        return env_vars

    except KeyError as e:
        print(f'Cannot extract env variables: {e}. Exiting.')


def save_price_history(price_history: dict, outdir: str, outfile: str) -> None:
    """Handle saving the results for price history."""

    create_dir(outdir) 
    destination = format_path(outdir, outfile)
    save_json(destination, price_history)
    log_info(f'Price history saved to {destination}')


def open_price_history(indir: str, infile: str) -> dict:
    """Handle opening the results for price history."""

    filepath = format_path(indir, infile)
    price_history = open_json(filepath)
    log_info(f'Price history loaded from {filepath}')

    return price_history


def save_cointegration(data: list, key: str, outdir: str, outfile: str) -> pd.DataFrame:
    """Handle saving the results for cointegration."""

    df = pd.DataFrame(data)
    df = df.sort_values(key, ascending=False)

    destination = format_path(outdir, outfile)
    save_csv(df, destination)
    log_info(f'Cointegration saved to {destination}')

    return df


def open_cointegration(indir: str, infile: str) -> dict:
    """Handle opening the results for cointegration."""

    filepath = format_path(indir, infile)
    try:
        cointegration = open_csv(filepath)
        log_info(f'Cointegration loaded from {filepath}')
        return cointegration
    except FileNotFoundError:
        log_error(f'Cointegration file not found at {filepath}')
        return False


def save_metrics(data: list, outdir: str, outfile: str) -> None:
    """Handle saving the results for metrics."""

    df = pd.DataFrame(data)

    if not df.empty:
        destination = format_path(outdir, outfile)
        save_csv(df, destination)
        log_info(f'Metrics saved to {destination}')

    return df


def open_metrics(indir: str, infile: str) -> dict:
    """Handle opening the results for metrics."""

    filepath = format_path(indir, infile)
    try:
        metrics = open_csv(filepath)
        log_info(f'Metrics loaded from {filepath}')
        return metrics
    except FileNotFoundError:
        log_error(f'Metrics file not found at {filepath}')
        return False
