import datetime
import decimal

import sqlalchemy
from sqlalchemy.orm import mapped_column, Mapped, declarative_base

DeclarativeBase = declarative_base()


class ExchangeRate(DeclarativeBase):
    __tablename__ = 'exchange_rates'

    id: Mapped[int] = mapped_column(name='id')
    date: Mapped[datetime.date] = mapped_column(sqlalchemy.DATE(), name='date', nullable=False, key='date')
    timestamp: Mapped[datetime.datetime] = mapped_column(sqlalchemy.TIMESTAMP(timezone=True), name='timestamp', nullable=False, primary_key=True, key='timestamp')
    epoch_seconds: Mapped[int] = mapped_column(sqlalchemy.BIGINT(), name='epoch_seconds', nullable=False, key='epoch_seconds')
    base: Mapped[str] = mapped_column(sqlalchemy.String(5), name='base', nullable=False, primary_key=True, key='base')
    to: Mapped[str] = mapped_column(sqlalchemy.String(5), name='to', nullable=False, primary_key=True, key='to')
    rate: Mapped[decimal.Decimal] = mapped_column(sqlalchemy.DECIMAL, name='rate', nullable=False)

    def __repr__(self):
        return ('id: {}, date: {}, timestamp: {}, base: {}, to: {}, rate: {}'
                .format(self.id, self.date, self.timestamp, self.base, self.to, self.rate))
