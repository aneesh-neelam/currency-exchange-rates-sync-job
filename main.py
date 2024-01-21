#!/bin/env python3

import json
import os
from datetime import datetime

import requests
import rollbar
import sqlalchemy
from sqlalchemy.orm import Session

import db

base_url = 'http://api.exchangeratesapi.io/v1/'
latest_rates_url = base_url + 'latest'


def sync():
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError('Cannot find Exchange Rates API Key in Environment Variables')

    rates_json = get_rates(api_key)
    print('Fetched Currency Exchange Rates: ' + str(rates_json))

    # Parse API Response
    date_str = rates_json['date']
    rate_date = datetime.strptime(date_str, '%Y-%m-%d')
    epoch_seconds = rates_json['timestamp']
    date_time = datetime.fromtimestamp(epoch_seconds)
    base_currency_code = rates_json['base']
    rate_dict = rates_json['rates']

    db_credentials = get_database_credentials()
    db_url = db_credentials['url']
    engine = sqlalchemy.create_engine(url=db_url, client_encoding='utf8', echo=True)
    with Session(engine) as session:
        for to_currency, rate in rate_dict.items():
            exchange_rate = db.ExchangeRate(date=rate_date, epoch_seconds=epoch_seconds, timestamp=date_time,
                                            base=base_currency_code, to=to_currency,
                                            rate=rate)
            session.add(exchange_rate)
        session.commit()

    return rates_json['timestamp']


def get_rates(api_key, base_currency=None, other_currencies=None):
    print('Fetching Currency Exchange Rates from API')
    url_params = dict()
    url_params['access_key'] = api_key
    if base_currency is not None:
        url_params['base'] = base_currency
    if other_currencies is not None or other_currencies:
        url_params['symbols'] = ','.join(other_currencies)

    response = requests.get(latest_rates_url, params=url_params, timeout=30.0)

    if response.status_code != 200:
        raise RuntimeError('Received status code from API: ' + str(response.status_code))
    rates_json = response.json()
    if rates_json['success'] is not True:
        raise RuntimeError('Received non-success status from API')

    print('Successfully fetched Currency Exchange Rates from API')
    return rates_json


def get_api_key():
    return os.environ.get('EXCHANGE_RATES_API_KEY')


def get_database_credentials():
    credentials = {
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'database': os.environ.get('DB_DATABASE'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
    }
    credentials['url'] = "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}?sslmode=require".format(
        host=credentials['host'], port=credentials['port'], database=credentials['database'], user=credentials['user'],
        password=credentials['password'])
    return credentials


def get_rollbar_token():
    return os.environ.get('ROLLBAR_TOKEN')


def get_deployment_environment():
    return os.environ.get('DEPLOYMENT_ENVIRONMENT')


def get_code_version():
    return os.environ.get('CODE_VERSION')


def get_sample_rates():
    with open('sample/response.json') as sample_rates_file:
        return json.load(sample_rates_file)


# Execution start point
if __name__ == '__main__':
    code_version = get_code_version()
    deployment_env = get_deployment_environment()
    rollbar_token = get_rollbar_token()
    rollbar.init(
        access_token=rollbar_token,
        environment=deployment_env,
        code_version=code_version
    )
    rollbar.report_message(message='Rollbar is configured correctly', level='info')

    try:
        timestamp = sync()
        rollbar_data = {
            'timestamp': timestamp
        }
        rollbar.report_message(message='Successfully synced Currency Exchange Rates', level='info',
                               extra_data=rollbar_data)
    except BaseException as e:
        rollbar.report_exc_info()
        raise e
