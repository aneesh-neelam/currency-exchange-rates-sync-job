#!/bin/env python3

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import requests
import rollbar
import sentry_sdk
import sqlalchemy
from sqlalchemy.orm import Session

import db


def parse_api_response(rates_json):
    date_str = rates_json['date']
    rate_date = datetime.strptime(date_str, '%Y-%m-%d')
    epoch_seconds = rates_json['timestamp']
    date_time = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
    base_currency_code = rates_json['base']
    rate_dict = rates_json['rates']

    return rate_date, epoch_seconds, date_time, base_currency_code, rate_dict


def insert_new_rates(session, rate_date, epoch_seconds, date_time, base_currency_code, rate_dict):
    logging.log(logging.INFO, 'Inserting %d new Currency Exchange Rates from API into Database',
                len(rate_dict))
    for to_currency, rate in rate_dict.items():
        exchange_rate = db.ExchangeRate(date=rate_date, epoch_seconds=epoch_seconds, timestamp=date_time,
                                        base=base_currency_code, to=to_currency,
                                        rate=rate)
        logging.log(logging.INFO, 'Inserting new Currency Exchange Rate from API into Database: %s',
                    exchange_rate)
        session.add(exchange_rate)
    session.commit()
    logging.log(logging.INFO, 'Inserted %d new Currency Exchange Rates from API into Database',
                len(rate_dict))


def cleanup_old_rates(session, oldest_rate_retention_date):
    logging.log(logging.INFO, 'Cleaning up old Currency Exchange Rates from Database, '
                              'older than Retention Date: %s',
                oldest_rate_retention_date)
    delete_stmt = sqlalchemy.delete(db.ExchangeRate).where(db.ExchangeRate.date.__lt__(oldest_rate_retention_date))
    session.execute(delete_stmt)
    session.commit()
    logging.log(logging.INFO, 'Cleaned up old Currency Exchange Rates from Database, '
                              'older than Retention Date: %s',
                oldest_rate_retention_date)


def sync_rates():
    latest_rates_url = get_exchange_rates_api_latest_rates_url()
    logging.log(logging.INFO, 'Using Exchange Rates API at: %s', latest_rates_url)

    api_key = get_api_key()
    if not api_key:
        logging.log(logging.CRITICAL, 'Cannot find Exchange Rates API Key for URL: %s in Environment Variables',
                    latest_rates_url)
        raise RuntimeError(
            'Cannot find Exchange Rates API Key for URL: {} in Environment Variables'.format(latest_rates_url))

    rates_json = get_rates(latest_rates_url=latest_rates_url, api_key=api_key)
    logging.log(logging.INFO, 'Fetched Currency Exchange Rates: %s', rates_json)

    rate_date, epoch_seconds, date_time, base_currency_code, rate_dict = parse_api_response(rates_json)

    retention_period_days = int(get_retention_period_days())
    oldest_rate_retention_date = (rate_date - timedelta(days=retention_period_days)).date()
    logging.log(logging.INFO, 'Oldest Currency Exchange Rate Retention Date: %s',
                oldest_rate_retention_date)

    db_credentials = get_database_credentials()
    db_url = db_credentials['url']
    engine = sqlalchemy.create_engine(url=db_url, client_encoding='utf8', echo=True)
    with Session(engine) as session:
        insert_new_rates(session, rate_date, epoch_seconds, date_time, base_currency_code, rate_dict)
        cleanup_old_rates(session, oldest_rate_retention_date)

    return {
        'timestamp': rates_json['timestamp'],
        'rate_date': str(rate_date),
        'oldest_rate_retention_date': str(oldest_rate_retention_date),
        'base_currency': base_currency_code,
        'rates_count': len(rate_dict),
    }


def get_rates(latest_rates_url, api_key, base_currency=None, other_currencies=None):
    logging.log(logging.INFO, 'Fetching Currency Exchange Rates from API: %s',
                latest_rates_url)
    url_params = dict()
    url_params['access_key'] = api_key
    if base_currency is not None:
        url_params['base'] = base_currency
    if other_currencies is not None or other_currencies:
        url_params['symbols'] = ','.join(other_currencies)

    response = requests.get(latest_rates_url, params=url_params, timeout=30.0)

    if response.status_code != 200:
        logging.log(logging.ERROR, 'Received unsupported HTTP status code: %d from API: %s',
                    response.status_code, latest_rates_url)
        raise RuntimeError('Received unsupported HTTP status code: {} from API: {}'.format(str(response.status_code),
                                                                                           latest_rates_url))
    rates_json = response.json()
    if rates_json['success'] is not True:
        logging.log(logging.ERROR, 'Received non-Success status: %s from API: %s',
                    rates_json['success'], latest_rates_url)
        raise RuntimeError('Received non-success status: {} from API: {}'.format(str(rates_json['success']),
                                                                                 latest_rates_url))

    logging.log(logging.INFO, 'Successfully fetched Currency Exchange Rates from API: %s',
                latest_rates_url)
    return rates_json


def get_api_key():
    return os.environ.get('EXCHANGE_RATES_API_KEY')


def get_database_credentials():
    credentials = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', '5432'),
        'database': os.environ.get('DB_DATABASE', 'postgres'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'example'),
        'sslmode': os.environ.get('DB_SSL_MODE', 'prefer'),
    }
    credentials['url'] = "postgresql+psycopg://{user}:{password}@{host}:{port}/{database}?sslmode={sslmode}".format(
        host=credentials['host'], port=credentials['port'], database=credentials['database'], user=credentials['user'],
        password=credentials['password'], sslmode=credentials['sslmode'])
    return credentials


def get_rollbar_token():
    return os.environ.get('ROLLBAR_TOKEN')


def get_sentry_dsn():
    return os.environ.get('SENTRY_DSN')


def get_deployment_environment():
    return os.environ.get('DEPLOYMENT_ENVIRONMENT', 'Development')


def get_code_version():
    return os.environ.get('CODE_VERSION', 'dev')


def get_retention_period_days():
    return os.environ.get('RETENTION_PERIOD_DAYS', '370')


def get_exchange_rates_api_latest_rates_url():
    return os.environ.get('EXCHANGE_RATES_API_LATEST_RATES_URL', 'http://api.exchangeratesapi.io/v1/' + 'latest')


def get_log_level():
    return os.environ.get('LOG_LEVEL', 'DEBUG')


def get_sample_rates():
    with open('sample/response.json') as sample_rates_file:
        return json.load(sample_rates_file)


# Execution start point
if __name__ == '__main__':
    log_level = get_log_level()
    print('Setting up Logger with Log Level: {}'.format(log_level))
    logging.basicConfig(level=log_level, stream=sys.stdout,
                        format='{asctime} {levelname} {pathname}:{lineno} {message}',
                        style='{', encoding='utf-8')

    logging.log(logging.INFO, 'Started Currency Exchange Rates Sync Job')

    code_version = get_code_version()
    deployment_env = get_deployment_environment()
    rollbar_token = get_rollbar_token()
    rollbar.init(
        access_token=rollbar_token,
        environment=deployment_env,
        code_version=code_version
    )
    sentry_dsn = get_sentry_dsn()
    sentry_sdk.init(
        dsn=sentry_dsn,
        shutdown_timeout=5,
        debug=True,
        send_default_pii=True, # There is no PII anyway
        attach_stacktrace=True,
        enable_tracing=True,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        # Environment
        environment=deployment_env,
        # Release
        release=code_version,
    )

    try:
        with sentry_sdk.monitor(monitor_slug='currency-exchange-rates-sync-job'):
            result = sync_rates()
        rollbar_data = {
            'timestamp': result['timestamp'],
            'base_currency': result['base_currency'],
            'rate_date': result['rate_date'],
            'oldest_rate_retention_date': result['oldest_rate_retention_date'],
            'rates_count': result['rates_count'],
        }

        logging.log(logging.INFO,
                    'Successfully synced %d Currency Exchange Rates against Base Currency: %s; '
                    'for Date: %s, Timestamp: %s; '
                    'and cleaned up stored Currency Exchange Rates older than Retention Date: %s',
                    result['rates_count'], result['base_currency'], result['rate_date'], result['timestamp'],
                    result['oldest_rate_retention_date'])
        rollbar.report_message(message='Successfully synced Currency Exchange Rates, '
                                       'and cleaned up stored Currency Exchange Rates older than Retention Date',
                               level='info', extra_data=rollbar_data)
    except BaseException as e:
        rollbar.report_exc_info()
        raise e
