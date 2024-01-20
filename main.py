#!/bin/env python3

import os

import requests

base_url = 'http://api.exchangeratesapi.io/v1/'
latest_rates_url = base_url + 'latest'


def sync():
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError('Cannot find API Key in Environment Variables')
    base_currency = None
    other_currencies = None
    rates_json = get_rates(api_key, base_currency=base_currency, other_currencies=other_currencies)
    print(str(rates_json))
    # TODO: Persist to Database
    # TODO: Set up Rollbar for Errors

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
    return os.environ.get('API_KEY')


# Execution start point
if __name__ == '__main__':
    sync()
