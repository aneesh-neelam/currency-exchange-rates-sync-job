import datetime
import decimal

import sqlalchemy
from sqlalchemy.orm import mapped_column, Mapped, declarative_base

DeclarativeBase = declarative_base()


class ExchangeRate(DeclarativeBase):
    __tablename__ = 'exchange_rates'

    id: Mapped[int] = mapped_column(sqlalchemy.Identity(), name='id', unique=True, index=True)
    date: Mapped[datetime.date] = mapped_column(sqlalchemy.DATE(), name='date', nullable=False, index=True, key='date')
    timestamp: Mapped[datetime.datetime] = mapped_column(sqlalchemy.TIMESTAMP(timezone=True), name='timestamp', nullable=False, primary_key=True, index=True, key='timestamp')
    epoch_seconds: Mapped[int] = mapped_column(sqlalchemy.BIGINT(), name='epoch_seconds', nullable=False, index=True, key='epoch_seconds')
    base: Mapped[str] = mapped_column(sqlalchemy.String(5), name='base', nullable=False, primary_key=True, index=True, key='base')
    to: Mapped[str] = mapped_column(sqlalchemy.String(5), name='to', nullable=False, primary_key=True, index=True, key='to')
    rate: Mapped[decimal.Decimal] = mapped_column(sqlalchemy.DECIMAL, name='rate', nullable=False)

    def __repr__(self):
        return f'<ExchangeRate: {self}'
