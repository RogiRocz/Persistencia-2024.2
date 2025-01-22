from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Clientes, Estoque, Produtos, Vendas, Fornecedores
from db_connect import get_db

app = FastAPI()

@app.get('/')
def home():
    return "Ola: Mundo"

@app.get('/produtos')
def get_all_produtos(db: Session = Depends(get_db)):
    return db.query(Produtos).all

@app.get('/produtos/{id_produto}')
def get_produto(id_produto: int, db: Session = Depends(get_db)):
    return db.query(Produtos).filter_by(ID_Produto = id_produto)

@app.post('/produtos')
def create_produto(nome: str, valor_un: float, db: Session = Depends(get_db)):
    produto = Produtos(nome = nome, valor_unitario = valor_un)
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto

@app.put('/Produtos/{id_produto}')
def update_produto(id_produto: int, nome: str, valor_un: float, db: Session = Depends(get_db)):
    old_produto = db.query(Produtos).filter_by(ID_Produto = id_produto)
    old_produto.update(nome = nome, valor_unitario = valor_un)
    db.commit()
    db.refresh(old_produto)
    return get_produto(id_produto, db)

@app.delete('/Produtos/{id_produto}')
def delete_produto(id_produto: int, db: Session = Depends(get_db)):
    return db.query(Produtos).filter_by(ID_Produto = id_produto).delete(synchronize_session=False)