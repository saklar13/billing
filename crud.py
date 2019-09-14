import datetime
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session, aliased

import models
import schemas


def get_currency_by_name(db: Session, currency_name: str) -> models.Currency:
    return db.query(models.Currency).filter(models.Currency.name == currency_name).one()


def get_customer_by_name(
    db: Session, full_name: str, for_update: bool = False
) -> models.CustomersWallet:
    if for_update:
        return (
            db.query(models.CustomersWallet)
            .with_for_update()
            .filter(models.CustomersWallet.full_name == full_name)
            .one_or_none()
        )
    else:
        return (
            db.query(models.CustomersWallet)
            .filter(models.CustomersWallet.full_name == full_name)
            .one_or_none()
        )


def get_customers_by_names(
    db: Session, full_names: List[str]
) -> List[models.CustomersWallet]:
    return (
        db.query(models.CustomersWallet)
        .filter(models.CustomersWallet.full_name.in_(full_names))
        .all()
    )


def create_customer(
    db: Session, customers_wallet_schema: schemas.CustomersWalletCreate
) -> models.CustomersWallet:
    db_currency = get_currency_by_name(db, customers_wallet_schema.currency.value)
    customers_wallet_schema.currency = db_currency
    db_customer = models.CustomersWallet(**customers_wallet_schema.dict())

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)

    return db_customer


def get_currency_rate(
    db: Session, currency_name: str, date: datetime.date = None
) -> Decimal:
    if date is None:
        date = datetime.date.today()

    if currency_name == schemas.CurrencyEnum.usd:
        return Decimal(1)

    return (
        db.query(models.CurrencyRate)
        .filter(models.CurrencyRate.date == date)
        .join(models.CurrencyRate.currency)
        .filter_by(name=currency_name)
        .value(models.CurrencyRate.rate)
    )


def convert_currencies(
    db: Session, from_currency_name: str, to_currency_name: str, amount: Decimal
) -> Decimal:
    rate = get_currency_rate(db, from_currency_name)
    rate /= get_currency_rate(db, to_currency_name)

    return round(Decimal(amount * rate), 2)


def create_transaction_record(
    db: Session,
    to_customer_wallet: models.CustomersWallet,
    to_amount: Decimal,
    from_amount: Decimal,
    from_currency: models.Currency,
    from_customer_wallet: models.CustomersWallet = None,
):
    db_transaction = models.Transaction(
        from_customer_wallet=from_customer_wallet,
        to_customer_wallet=to_customer_wallet,
        from_amount=from_amount,
        to_amount=to_amount,
        from_currency=from_currency,
    )

    db.add(db_transaction)


def get_transactions(
    db: Session, customer_transaction_schema: schemas.CustomerTransactionsIn
) -> List[models.Transaction]:
    customer_wallet_alias = aliased(models.CustomersWallet)

    name = customer_transaction_schema.customer_name
    query = (
        db.query(models.Transaction)
        .join(models.Transaction.to_customer_wallet)
        .outerjoin(customer_wallet_alias, models.Transaction.from_customer_wallet)
        .filter(
            (models.CustomersWallet.full_name == name)
            | (customer_wallet_alias.full_name == name)
        )
    )
    if customer_transaction_schema.from_date:
        query = query.filter(
            models.Transaction.date_time >= customer_transaction_schema.from_date
        )
    if customer_transaction_schema.to_date:
        query = query.filter(
            models.Transaction.date_time <= customer_transaction_schema.to_date
        )

    return query.all()


def add_to_wallet(
    db: Session,
    customer_wallet: models.CustomersWallet,
    to_amount: Decimal,
    from_amount: Decimal,
    from_currency: models.Currency,
):
    db.query(models.CustomersWallet).filter(
        models.CustomersWallet.full_name == customer_wallet.full_name
    ).update({"amount": models.CustomersWallet.amount + to_amount})

    create_transaction_record(
        db,
        to_customer_wallet=customer_wallet,
        to_amount=to_amount,
        from_amount=from_amount,
        from_currency=from_currency,
    )

    db.commit()


def transfer_from_customer_to_customer(
    db: Session,
    from_customer: models.CustomersWallet,
    to_customer: models.CustomersWallet,
    from_amount: Decimal,
    to_amount: Decimal,
):
    db.query(models.CustomersWallet).filter(
        models.CustomersWallet.full_name == from_customer.full_name
    ).update({"amount": models.CustomersWallet.amount - from_amount})
    db.query(models.CustomersWallet).filter(
        models.CustomersWallet.full_name == to_customer.full_name
    ).update({"amount": models.CustomersWallet.amount + to_amount})

    create_transaction_record(
        db,
        from_customer_wallet=from_customer,
        to_customer_wallet=to_customer,
        to_amount=to_amount,
        from_amount=from_amount,
        from_currency=from_customer.currency,
    )

    db.commit()


def add_currency_rate(
    db: Session, set_currency_schema: schemas.CurrencyRateCreate
) -> models.CurrencyRate:
    db_currency = get_currency_by_name(db, set_currency_schema.currency.value)
    set_currency_schema.currency = db_currency
    db_currency_rate = models.CurrencyRate(**set_currency_schema.dict())

    db.add(db_currency_rate)
    db.commit()
    db.refresh(db_currency_rate)

    return db_currency_rate
