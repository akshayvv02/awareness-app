import logging
import pandas as pd
from datetime import datetime
from app.routes import data_refresh
import pytz

def call_endpoint():
    logging.info('----------- refresh call initiated ----------')
    # Call the data_refresh function from routes.py
    try:
        logging.info('--------- calling data_refresh endpoint function ---------')
        response = data_refresh()
        logging.info(f'---------Data refresh response: {response} -----------')
    except Exception as e:
        logging.error(f'Error during data refresh call: {str(e)}')
    est = pytz.timezone('US/Eastern')
    current_timestamp = datetime.now(est).strftime('%Y-%m-%d %I:%M:%S %p')
    logging.info(f'--------- New entry added: {current_timestamp}, True ---------')
