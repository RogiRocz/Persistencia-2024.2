from decimal import Decimal
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from http import HTTPStatus
from sqlalchemy.orm import Session
from db_models import Clientes, Estoque, Produtos, Vendas, Fornecedores
from db_connect import get_db
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, validator