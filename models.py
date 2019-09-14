import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from database import Base
from schemas import CurrencyEnum


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(CurrencyEnum), unique=True, index=True)


class CurrencyRate(Base):
    __tablename__ = "currency_rates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    rate = Column(Numeric)
    currency_id = Column(Integer, ForeignKey("currencies.id"))

    currency = relationship("Currency", lazy="joined")


class CustomersWallet(Base):
    __tablename__ = "customers_wallets"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), unique=True, index=True)
    country = Column(String(100))
    city = Column(String(100))
    currency_id = Column(Integer, ForeignKey("currencies.id"))
    amount = Column(Numeric(scale=2, decimal_return_scale=2), default=0)

    currency = relationship("Currency", uselist=False, lazy="joined")


class Transaction(Base):
    __tablename__ = "db_transactions"

    id = Column(Integer, primary_key=True, index=True)
    from_customer_wallet_id = Column(
        Integer, ForeignKey("customers_wallets.id"), index=True, nullable=True
    )
    to_customer_wallet_id = Column(
        Integer, ForeignKey("customers_wallets.id"), index=True
    )
    from_amount = Column(Numeric(scale=2, decimal_return_scale=2))
    to_amount = Column(Numeric(scale=2, decimal_return_scale=2))
    from_currency_id = Column(Integer, ForeignKey("currencies.id"))
    date_time = Column(DateTime, default=datetime.datetime.now)

    from_customer_wallet = relationship(
        "CustomersWallet", foreign_keys=[from_customer_wallet_id]
    )
    to_customer_wallet = relationship(
        "CustomersWallet", foreign_keys=[to_customer_wallet_id]
    )
    from_currency = relationship("Currency")
