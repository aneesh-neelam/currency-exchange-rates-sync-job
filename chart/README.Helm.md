# Usage 

* [Helm Values](currency-exchange-sync/README.md)
* Secrets: [sync-job](chart/currency-exchange-sync/secrets.json)

#### Install/Upgrade

* `helm install currency-exchange-sync . -n currency-exchange-sync`

* `helm upgrade currency-exchange-sync . -n currency-exchange-sync`

#### Run manually

* `kubectl create job --from=cronjob/currency-exchange-sync-fixed-eight-hour-cron currency-exchange-sync-fixed-eight-hour-cron-manual-1 -n currency-exchange-sync`
