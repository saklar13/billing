import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, condecimal


class CurrencyEnum(str, Enum):
    usd = "USD"
    eur = "EUR"
    cad = "CAD"
    cny = "CNY"


class CustomersWalletBase(BaseModel):
    full_name: str
    country: str
    city: str


class CustomersWalletCreate(CustomersWalletBase):
    currency: CurrencyEnum


class Currency(BaseModel):
    name: CurrencyEnum

    class Config:
        orm_mode = True


class CustomersWallet(CustomersWalletBase):
    currency: Currency
    amount: Decimal

    class Config:
        orm_mode = True


class ReplenishmentWallet(BaseModel):
    customer_name: str
    amount: condecimal(gt=Decimal(0))
    currency: CurrencyEnum


class Transfer(BaseModel):
    from_customer: str
    to_customer: str
    amount: condecimal(gt=Decimal(0))


class CurrencyRateBase(BaseModel):
    rate: condecimal(gt=Decimal(0))
    date: datetime.date = None


class CurrencyRateCreate(CurrencyRateBase):
    currency: CurrencyEnum


class CurrencyRate(CurrencyRateBase):
    currency: Currency

    class Config:
        orm_mode = True


class TransactionOutputFormatEnum(str, Enum):
    csv = "csv"
    xml = "xml"


class CustomerTransactionsIn(BaseModel):
    customer_name: str
    from_date: datetime.date = None
    to_date: datetime.date = None
    format: TransactionOutputFormatEnum = TransactionOutputFormatEnum.csv
