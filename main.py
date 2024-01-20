#!/bin/env python3

import os

import psycopg2
import requests
import rollbar

base_url = 'http://api.exchangeratesapi.io/v1/'
latest_rates_url = base_url + 'latest'


def sync():
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError('Cannot find Exchange Rates API Key in Environment Variables')
    base_currency = None
    other_currencies = None
    rates_json = get_rates(api_key, base_currency=base_currency, other_currencies=other_currencies)
    print(str(rates_json))
    db_credentials = get_database_credentials()
    db_connection = connect_to_database(db_credentials=db_credentials)
    # TODO: Persist to Database
    close_database_connection(db_connection)
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
    return {
        'host': os.environ.get('DB_HOST'),
        'port': os.environ.get('DB_PORT'),
        'database': os.environ.get('DB_DATABASE'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
    }


def get_rollbar_token():
    return os.environ.get('ROLLBAR_TOKEN')


def get_deployment_environment():
    return os.environ.get('DEPLOYMENT_ENVIRONMENT')


def get_code_version():
    return os.environ.get('CODE_VERSION')


def connect_to_database(db_credentials):
    try:
        db_connection = psycopg2.connect(database=db_credentials['database'],
                                         host=db_credentials['host'],
                                         user=db_credentials['user'],
                                         password=db_credentials['password'],
                                         port=db_credentials['port'])
        print('PostgreSQL Database connection initiated: ' + str(db_connection))
    except BaseException as error:
        raise RuntimeError('Could not connect to PostgreSQL database due to Error: `' + str(error) + '`')
    return db_connection


def close_database_connection(db_connection):
    db_connection.close()
    print('PostgreSQL Database connection closed: ' + str(db_connection))


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
