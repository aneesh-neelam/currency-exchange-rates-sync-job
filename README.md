# Sync-Job for Currency Exchange Rates

This simple Python project is a Sync Job for Currency Exchange Rates

### Docker

* Dockerfile: [Dockerfile](Dockerfile)
* Docker Compose: [compose.yaml](compose.yaml)
* Container Registries:
  * [Docker Hub](https://hub.docker.com/repository/docker/aneeshneelam/currency-exchange-sync/general): `aneeshneelam/currency-exchange-sync`
  * In-cluster registry: `macstation-ubuntu-1.local:30500/currency-exchange-sync` (kubelet: `container-registry.container-registry.svc.cluster.local:5000/currency-exchange-sync`)

#### Build and Push (multi-arch)

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag macstation-ubuntu-1.local:30500/currency-exchange-sync:2.3-prod \
  --tag macstation-ubuntu-1.local:30500/currency-exchange-sync:latest \
  --tag aneeshneelam/currency-exchange-sync:2.3-prod \
  --tag aneeshneelam/currency-exchange-sync:latest \
  --push .
```

### Database

The schema is managed manually via DDL, not by the ORM.

* DDL: [ddl.sql](ddl.sql)

Run the DDL against the target database before deploying:

```bash
kubectl -n postgresql port-forward svc/pg-cluster-rw 5432:5432 &

PGPASSWORD=$(kubectl -n postgresql get secret currencyexchangeratessync-db-credentials \
  -o jsonpath='{.data.password}' | base64 -d) \
  psql -h localhost -U currencyexchangeratessync -d currency_exchange_rates -f ddl.sql
```

#### Data Migration (from old database)

```bash
pg_dump -h <OLD_HOST> -U <OLD_USER> -d <OLD_DB> --data-only -t exchange_rates | \
  PGPASSWORD=$(kubectl -n postgresql get secret currencyexchangeratessync-db-credentials \
    -o jsonpath='{.data.password}' | base64 -d) \
  psql -h localhost -U currencyexchangeratessync -d currency_exchange_rates
```

### Kubernetes / Helm

* Readme: [README.Helm.md](chart/README.Helm.md)
* Chart: [currency-exchange-sync](chart/currency-exchange-sync)

#### Secrets

Secrets are managed outside of Helm (not committed to git).

**`currencyexchangeratessync-db-credentials`** — replicated from the `postgresql` namespace. Contains keys: `username`, `database`, `password`.

```bash
kubectl -n currency-exchange-rates-sync get secret currencyexchangeratessync-db-credentials
```

**`currency-exchange-rates-sync-secrets`** — created manually. Contains keys: `exchangeRatesAPIKey`, `rollbarToken`, `sentryDsn`.

```bash
kubectl -n currency-exchange-rates-sync create secret generic currency-exchange-rates-sync-secrets \
  --from-literal=exchangeRatesAPIKey='<API_KEY>' \
  --from-literal=rollbarToken='<ROLLBAR_TOKEN>' \
  --from-literal=sentryDsn='<SENTRY_DSN>'
```
