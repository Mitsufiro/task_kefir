import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_sqlalchemy import DBSessionMiddleware

from routers import auth

load_dotenv(".env")
app = FastAPI(title="KEFIR Service", version="0.0.1")
app.add_middleware(DBSessionMiddleware, db_url=os.environ["DATABASE_URL"])
app.include_router(auth.ROUTER)
