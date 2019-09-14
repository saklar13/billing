import datetime

from sqlalchemy import Table, event
from sqlalchemy.engine import Connection

import models
import schemas


def populate_db():
    for model in MAP_MODEL_TO_POPULATE_FUNC:
        event.listen(model.__table__, "after_create", populate_rows)


def populate_rows(target: Table, connection: Connection, **kw):
    rows = {
        model.__tablename__: rows for model, rows in MAP_MODEL_TO_POPULATE_FUNC.items()
    }[target.name]
    connection.execute(target.insert(), *rows)


MAP_MODEL_TO_POPULATE_FUNC = {
    models.Currency: [
        {"id": 1, "name": schemas.CurrencyEnum.usd},
        {"id": 2, "name": schemas.CurrencyEnum.eur},
        {"id": 3, "name": schemas.CurrencyEnum.cad},
        {"id": 4, "name": schemas.CurrencyEnum.cny},
    ],
    models.CurrencyRate: [
        {"id": 1, "date": datetime.date.today(), "rate": "1.10731", "currency_id": 2},
        {"id": 2, "date": datetime.date.today(), "rate": "0.753602", "currency_id": 3},
        {"id": 3, "date": datetime.date.today(), "rate": "0.141249", "currency_id": 4},
    ],
    models.CustomersWallet: [
        {
            "id": 1,
            "full_name": "Ivan Ivanov",
            "country": "Ukraine",
            "city": "Kyiv",
            "currency_id": 2,
        },
        {
            "id": 2,
            "full_name": "Petr Petrov",
            "country": "Ukraine",
            "city": "Kyiv",
            "currency_id": 4,
        },
        {
            "id": 3,
            "full_name": "Sergey Sergeev",
            "country": "Ukraine",
            "city": "Kyiv",
            "currency_id": 1,
        },
    ],
}
