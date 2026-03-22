# Usage

* [Helm Values](currency-exchange-sync/README.md)

#### Secrets

Secrets are **not** managed by Helm. Create them manually before deploying:

1. **Database password** — comes from `currencyexchangeratessync-db-credentials` (replicated from `postgresql` namespace).

2. **App secrets** — create manually:
   ```bash
   kubectl -n currency-exchange-rates-sync create secret generic currency-exchange-rates-sync-secrets \
     --from-literal=exchangeRatesAPIKey='<API_KEY>' \
     --from-literal=rollbarToken='<ROLLBAR_TOKEN>' \
     --from-literal=sentryDsn='<SENTRY_DSN>'
   ```

#### Install/Upgrade

```bash
helm install currency-exchange-rates-sync . -n currency-exchange-rates-sync
```

```bash
helm upgrade currency-exchange-rates-sync . -n currency-exchange-rates-sync
```

#### Run manually

```bash
kubectl create job --from=cronjob/currency-exchange-rates-sync currency-exchange-rates-sync-manual-1 \
  -n currency-exchange-rates-sync
```
