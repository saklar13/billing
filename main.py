from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import Response

import crud
import helpers
import models
import populate_db
import schemas
from database import SessionLocal, engine

populate_db.populate_db()
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


# Dependency
def get_db(request: Request):
    return request.state.db


@app.post("/create-customers-wallet", response_model=schemas.CustomersWallet)
def create_customer(
    customer_schema: schemas.CustomersWalletCreate, db: Session = Depends(get_db)
):
    db_customer = crud.get_customer_by_name(db, customer_schema.full_name)
    if db_customer:
        raise HTTPException(status_code=400, detail="User already registered")
    return crud.create_customer(db, customer_schema)


@app.post("/wallet/replenishment", response_model=schemas.CustomersWallet)
def replenishment(
    replenishment_schema: schemas.ReplenishmentWallet, db: Session = Depends(get_db),
):
    db_customer = crud.get_customer_by_name(
        db, replenishment_schema.customer_name
    )
    if not db_customer:
        raise HTTPException(status_code=400, detail="User doesn't exists")

    converted_amount = crud.convert_currencies(
        db,
        replenishment_schema.currency,
        db_customer.currency.name,
        replenishment_schema.amount,
    )
    db_currency = crud.get_currency_by_name(db, replenishment_schema.currency.value)
    crud.add_to_wallet(
        db,
        db_customer,
        converted_amount,
        replenishment_schema.amount,
        db_currency,
    )
    return crud.get_customer_by_name(db, replenishment_schema.customer_name)


@app.post("/wallet/transfer", response_model=List[schemas.CustomersWallet])
def transfer(transfer_schema: schemas.Transfer, db: Session = Depends(get_db)):
    from_db_customer = crud.get_customer_by_name(
        db, transfer_schema.from_customer, for_update=True
    )
    if not from_db_customer:
        raise HTTPException(status_code=400, detail="User doesn't exists")
    if from_db_customer.amount < transfer_schema.amount:
        raise HTTPException(status_code=400, detail="Few money to transfer")

    to_db_customer = crud.get_customer_by_name(
        db, transfer_schema.to_customer, for_update=True
    )
    if not to_db_customer:
        raise HTTPException(status_code=400, detail="User doesn't exists")

    converted_amount = crud.convert_currencies(
        db,
        from_db_customer.currency.name,
        to_db_customer.currency.name,
        transfer_schema.amount,
    )
    crud.transfer_from_customer_to_customer(
        db, from_db_customer, to_db_customer, transfer_schema.amount, converted_amount
    )

    return crud.get_customers_by_names(
        db, [transfer_schema.from_customer, transfer_schema.to_customer]
    )


@app.post("/customer_transactions")
def get_customer_transactions(
    customer_transactions_schema: schemas.CustomerTransactionsIn,
    db: Session = Depends(get_db),
):
    trs = crud.get_transactions(db, customer_transactions_schema)
    if customer_transactions_schema.format == schemas.TransactionOutputFormatEnum.csv:
        output = helpers.db_transactions_to_csv(trs)
    else:
        output = helpers.db_transactions_to_xml(trs)
    return Response(
        content=output, media_type=f"text/{customer_transactions_schema.format.value}"
    )


@app.post("/set-currency-rate", response_model=schemas.CurrencyRate)
def set_currency_rate(
    set_currency_schema: schemas.CurrencyRateCreate, db: Session = Depends(get_db)
):
    db_currency_rate = crud.get_currency_rate(
        db, set_currency_schema.currency.value, set_currency_schema.date
    )
    if db_currency_rate:
        raise HTTPException(status_code=400, detail="Currency rate already set")

    db_currency_rate = crud.add_currency_rate(db, set_currency_schema)
    return db_currency_rate


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
