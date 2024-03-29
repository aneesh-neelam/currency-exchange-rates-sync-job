
Currency-exchange-sync-cronjob
===========

A Helm chart for Currency Exchange Sync Cron Job on Kubernetes


## Configuration

The following table lists the configurable parameters of the Currency-exchange-sync-cronjob chart and their default values.

| Parameter                | Description             | Default        |
| ------------------------ | ----------------------- | -------------- |
| `cronjob.name` |  | `"currency-exchange-rates-sync"` |
| `cronjob.schedule` |  | `"0 0,3,6,9,12,15,18,21 * * *"` |
| `cronjob.id` |  | `"currency-exchange-rates-sync"` |
| `cronjob.timeZone` |  | `"Asia/Kolkata"` |
| `cronjob.exchangeRatesApiLatestRatesUrl` |  | `"http://api.exchangeratesapi.io/v1/latest"` |
| `cronjob.retentionPeriodDays` |  | `400` |
| `cronjob.env` |  | `"Production"` |
| `cronjob.logLevel` |  | `"INFO"` |
| `cronjob.version` |  | `"2.0-prod"` |
| `cronjob.metadata.namespace` |  | `"currency-exchange-sync"` |
| `cronjob.metadata.secret` |  | `"sync-job"` |
| `cronjob.restartPolicy` |  | `"Never"` |
| `cronjob.backoffLimit` |  | `1` |
| `cronjob.successfulJobsHistoryLimit` |  | `8` |
| `cronjob.failedJobsHistoryLimit` |  | `8` |
| `cronjob.image.repository` |  | `"registry.digitalocean.com/aneeshneelam-container-registry-sfo3/currency-exchange-sync"` |
| `cronjob.image.pullPolicy` |  | `"Always"` |
| `cronjob.image.imagePullSecrets` |  | `"aneeshneelam-container-registry-sfo3"` |
| `cronjob.image.restartPolicy` |  | `"Never"` |
| `cronjob.image.concurrencyPolicy` |  | `"Forbid"` |
| `cronjob.resources.requests.cpu` |  | `"100m"` |
| `cronjob.resources.requests.memory` |  | `"64Mi"` |
| `cronjob.resources.limits.cpu` |  | `"500m"` |
| `cronjob.resources.limits.memory` |  | `"128Mi"` |



---
_Documentation generated by [Frigate](https://frigate.readthedocs.io)._

