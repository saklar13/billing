import csv
import io
from typing import List

import xmltodict

import models


def db_transactions_to_csv(db_transactions: List[models.Transaction]) -> str:
    dicts = db_transactions_to_dicts(db_transactions)
    if not dicts:
        return ""

    buffer = io.StringIO()
    fieldnames = list(dicts[0].keys())

    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for dict_ in dicts:
        writer.writerow(dict_)

    output = buffer.getvalue()
    return output


def db_transactions_to_xml(db_transactions: List[models.Transaction]) -> str:
    dicts = db_transactions_to_dicts(db_transactions)
    output = xmltodict.unparse({"root": {"transaction": dicts}})
    return output


def db_transactions_to_dicts(db_transactions: List[models.Transaction]) -> List[dict]:
    transactions_dicts = []

    for db_transaction in db_transactions:
        transaction_data = {
            "from_customer": (
                db_transaction.from_customer_wallet.full_name
                if db_transaction.from_customer_wallet
                else "outside"
            ),
            "from_amount": db_transaction.from_amount,
            "from_currency": db_transaction.from_currency.name.value,
            "to_customer": db_transaction.to_customer_wallet.full_name,
            "to_amount": db_transaction.to_amount,
            "to_currency": db_transaction.to_customer_wallet.currency.name.value,
            "date_time": db_transaction.date_time,
        }

        transactions_dicts.append(transaction_data)

    return transactions_dicts
