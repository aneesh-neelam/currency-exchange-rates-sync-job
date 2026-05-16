## Currency Rates Sync — Known Issues and Recommendations

### Python application

- Issue: `symbols` query param condition may send empty value or be mis-evaluated
  - Evidence:
```93:101:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
def get_rates(latest_rates_url, api_key, base_currency=None, other_currencies=None):
    ...
    if base_currency is not None:
        url_params['base'] = base_currency
    if other_currencies is not None or other_currencies:
        url_params['symbols'] = ','.join(other_currencies)
```
  - Impact: May produce `symbols=` (empty) or include the param unintentionally.
  - Recommendation: Use `if other_currencies:` and validate non-empty list.

- Issue: `rate_date` parsed as `datetime` but stored/used as `DATE`
  - Evidence:
```18:26:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
def parse_api_response(rates_json):
    date_str = rates_json['date']
    rate_date = datetime.strptime(date_str, '%Y-%m-%d')
    ...
    return rate_date, epoch_seconds, date_time, base_currency_code, rate_dict
```
  - Impact: Type mismatch with `db.ExchangeRate.date` (DATE). Later code calls `.date()` on `rate_date` for retention calcs, which expects a `date`.
  - Recommendation: `rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()`.

- Issue: Verbose SQLAlchemy engine logs hard-coded on
  - Evidence:
```77:83:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
engine = sqlalchemy.create_engine(url=db_url, client_encoding='utf8', echo=True)
```
  - Impact: Noisy logs in production, potential performance overhead.
  - Recommendation: Make `echo` configurable (env var) or tie to log level.

- Issue: Default API URL uses HTTP instead of HTTPS
  - Evidence:
```161:163:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
def get_exchange_rates_api_latest_rates_url():
    return os.environ.get('EXCHANGE_RATES_API_LATEST_RATES_URL', 'http://api.exchangeratesapi.io/v1/' + 'latest')
```
  - Impact: Unencrypted transport by default.
  - Recommendation: Default to `https://` and update Helm/Compose defaults accordingly.

- Issue: Overly broad exception handling
  - Evidence:
```211:233:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
    try:
        with sentry_sdk.monitor(monitor_slug='currency-exchange-rates-sync-job'):
            result = sync_rates()
        ...
    except BaseException as e:
        rollbar.report_exc_info()
        raise e
```
  - Impact: Catches `SystemExit`/`KeyboardInterrupt` and similar.
  - Recommendation: Catch `Exception` instead; allow process-level interrupts to pass through.

- Issue: Telemetry init not gated on presence of credentials
  - Evidence:
```184:209:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
rollbar.init(
    access_token=rollbar_token,
    ...
)
sentry_sdk.init(
    dsn=sentry_dsn,
    ...
)
```
  - Impact: May error out when env vars are empty/missing.
  - Recommendation: Only initialize Rollbar/Sentry when env vars are non-empty.

- Issue: Non-idiomatic comparison in cleanup query
  - Evidence:
```44:53:/Users/aneeshneelam/Developer/Git/currency-rates-sync/main.py
delete_stmt = sqlalchemy.delete(db.ExchangeRate).where(db.ExchangeRate.date.__lt__(oldest_rate_retention_date))
```
  - Impact: Works, but less readable.
  - Recommendation: Use `db.ExchangeRate.date < oldest_rate_retention_date`.

### Database model

- Issue: Mixed primary key strategy; separate unique `id` with composite primary key
  - Evidence:
```10:20:/Users/aneeshneelam/Developer/Git/currency-rates-sync/db.py
class ExchangeRate(DeclarativeBase):
    __tablename__ = 'exchange_rates'

    id: Mapped[int] = mapped_column(sqlalchemy.Identity(), name='id', unique=True, index=True)
    date: Mapped[datetime.date] = mapped_column(sqlalchemy.DATE(), name='date', nullable=False, index=True, key='date')
    timestamp: Mapped[datetime.datetime] = mapped_column(sqlalchemy.TIMESTAMP(timezone=True), name='timestamp', nullable=False, primary_key=True, index=True, key='timestamp')
    epoch_seconds: Mapped[int] = mapped_column(sqlalchemy.BIGINT(), name='epoch_seconds', nullable=False, index=True, key='epoch_seconds')
    base: Mapped[str] = mapped_column(sqlalchemy.String(5), name='base', nullable=False, primary_key=True, index=True, key='base')
    to: Mapped[str] = mapped_column(sqlalchemy.String(5), name='to', nullable=False, primary_key=True, index=True, key='to')
    rate: Mapped[decimal.Decimal] = mapped_column(sqlalchemy.DECIMAL, name='rate', nullable=False)
```
  - Impact: Complicates upserts/migrations; unclear source of truth for identity.
  - Recommendation: Choose one:
    - Make `id` the sole primary key; add a unique constraint on `(timestamp, base, to)`.
    - Or remove `id` and rely on composite primary key.

- Issue: `DECIMAL` without precision/scale; no conversion to `Decimal`
  - Impact: Floats from API may lose precision; implicit conversion may be inconsistent.
  - Recommendation: Use `Numeric(18, 8)` (or appropriate) and convert rates via `Decimal(str(rate))` before persisting.

- Issue: No migrations or schema management
  - Impact: Assumes table pre-exists; brittle deployments.
  - Recommendation: Introduce Alembic migrations, or create tables on startup with explicit opt-in.

### Docker/Compose

- Issue: Copying source after switching to non-root; and entrypoint via script path
  - Evidence:
```41:49:/Users/aneeshneelam/Developer/Git/currency-rates-sync/Dockerfile
# Switch to the non-privileged user to run the application.
USER appuser

# Copy the source code into the container.
COPY . .

# Run the application.
CMD ["./main.py"]
```
  - Impact: `COPY` may fail due to permissions; `./main.py` may not be executable.
  - Recommendation: Copy as root, `chown -R appuser:appuser /app`, then `USER appuser`; prefer `CMD ["python", "main.py"]`.

- Issue: BuildKit-dependent `--mount=type=bind` for `requirements.txt`
  - Evidence:
```33:40:/Users/aneeshneelam/Developer/Git/currency-rates-sync/Dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install -r requirements.txt
```
  - Impact: Fails where BuildKit isn’t enabled.
  - Recommendation: Use `COPY requirements.txt .` prior to install for portability; keep cache mount optional.

- Issue: Default API URL uses HTTP in Compose and Helm values
  - Evidence:
```20:23:/Users/aneeshneelam/Developer/Git/currency-rates-sync/compose.yaml
EXCHANGE_RATES_API_LATEST_RATES_URL: http://api.exchangeratesapi.io/v1/latest
```
```6:7:/Users/aneeshneelam/Developer/Git/currency-rates-sync/chart/currency-exchange-sync/values.yaml
exchangeRatesApiLatestRatesUrl: http://api.exchangeratesapi.io/v1/latest
```
  - Recommendation: Switch to `https://` if supported by the provider.

### Helm chart

- Issue: Inconsistent value hierarchy (placing policy fields under `image`)
  - Evidence:
```1:9:/Users/aneeshneelam/Developer/Git/currency-rates-sync/chart/currency-exchange-sync/templates/cronjob.yaml
concurrencyPolicy: {{ $.Values.cronjob.image.concurrencyPolicy }}
...
restartPolicy: {{ $.Values.cronjob.image.restartPolicy }}
```
```21:27:/Users/aneeshneelam/Developer/Git/currency-rates-sync/chart/currency-exchange-sync/values.yaml
image:
  ...
  restartPolicy: Never
  concurrencyPolicy: Forbid
```
  - Impact: Semantic mismatch; policies are not image attributes and duplication risks drift.
  - Recommendation: Move `concurrencyPolicy` and `restartPolicy` to appropriate levels under `cronjob` (spec/template) and remove from `image` block.

### Testing gaps

- Missing tests for:
  - `get_rates` error paths, symbol handling, and timeout/HTTP errors.
  - DB persistence type/precision checks (e.g., `date` type, `Decimal` conversion).
  - Engine creation/config and cleanup behavior.

---

### Quick-fix checklist

- [ ] Change `if other_currencies is not None or other_currencies:` to `if other_currencies:`
- [ ] Parse `rate_date` with `.date()`
- [ ] Make SQLAlchemy `echo` configurable
- [ ] Default API URL to `https://`
- [ ] Catch `Exception` instead of `BaseException`
- [ ] Gate Rollbar/Sentry initialization on non-empty env vars
- [ ] Decide on single primary key strategy and add unique constraints as needed
- [ ] Set `rate` to `Numeric(precision=18, scale=8)` and convert inputs to `Decimal`
- [ ] Update Dockerfile to copy as root, chown, and use `CMD ["python", "main.py"]`
- [ ] Replace BuildKit bind mount with `COPY requirements.txt .`
- [ ] Move Helm `concurrencyPolicy`/`restartPolicy` out of `image` block
- [ ] Add tests for error paths, precision, and type handling


