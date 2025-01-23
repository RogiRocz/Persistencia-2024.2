from fastapi import Depends, HTTPException, APIRouter
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from db_connect import get_db
from db_models import Produtos
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from decimal import Decimal
from pagination import PaginationParams

class ProdutoPy(BaseModel):
    nome: str
    valor_unitario: Decimal = Field(max_digits=10, decimal_places=2)
    
    @validator('valor_unitario')
    def validate_valor_unitario(cls, value):
        value_str = str(value)
        if len(value_str.replace('.', '')) > 10:
            raise ValueError('O valor unitário não pode ter mais de 10 dígitos no total.')
        if '.' in value_str and len(value_str.split('.')[1]) > 2:
            raise ValueError('O valor unitário não pode ter mais de 2 casas decimais.')
        return value

def route_produtos(pref: str):
    router = APIRouter(prefix=f'/{pref}', tags=[pref])

    @router.get('/')
    def get_all_produtos(db: Session = Depends(get_db)):
        return db.query(Produtos).order_by(Produtos.ID_Produto).all()
    
    @router.get('/')
    def get_all_produtos_pagination(pag: PaginationParams = Depends(), db: Session = Depends(get_db)):
        offset = (pag.page - 1) * pag.limit
        produtos = db.query(Produtos).offset(offset).limit(pag.limit).all()
        total_produtos = db.query(Produtos).count()
        total_pages = (total_produtos + pag.limit - 1) // pag.limit
        
        return {'data': produtos, 'pagination': {'page': pag.page, 'limit': pag.limit, 'total_produtos': total_produtos, 'total_pages': total_pages}}

    @router.get('/{id_produto}')
    def get_produto(id_produto: int, db: Session = Depends(get_db)):
        if not id_produto:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')    
        
        try:
            query = db.query(Produtos).filter_by(ID_Produto = id_produto).first() 
            if query is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
        except HTTPException as e:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao retornar o produto. Erro: {str(e)}')
        return query

    @router.post('/')
    def create_produto(produto_req: ProdutoPy, db: Session = Depends(get_db)):
        if not produto_req.nome:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,detail="O nome do produto não pode estar vazio.")
        if produto_req.valor_unitario <= 0:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,detail="O valor unitário deve ser maior que zero.")
        
        try:
            produto = Produtos(nome=produto_req.nome, valor_unitario=produto_req.valor_unitario)
            db.add(produto)
            db.commit()
            db.refresh(produto)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao criar produto no banco de dados: {str(e)}")
        else:
            return produto

    @router.put('/{id_produto}')
    def update_produto(id_produto: int, produto_req: ProdutoPy, db: Session = Depends(get_db)):
        if not id_produto:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            produto_db = db.query(Produtos).filter_by(ID_Produto = id_produto).first()
            if produto_db is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            
            produto_antigo = {
                "ID_Produto": produto_db.ID_Produto,
                "nome": produto_db.nome,
                "valor_unitario": produto_db.valor_unitario
            }
            
            if produto_db.nome is not None:
                produto_db.nome = produto_req.nome
            if produto_db.valor_unitario is not None:
                produto_db.valor_unitario = produto_req.valor_unitario
                
            db.commit()
            db.refresh(produto_db)
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar o produto no banco de dados: {str(e)}")
        else:
            return produto_antigo

    @router.delete('/{id_produto}')
    def delete_produto(id_produto: int, db: Session = Depends(get_db)):
        if not id_produto:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        try:
            del_produto = db.query(Produtos).filter_by(ID_Produto = id_produto).first()
            if del_produto is None:
                raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID não encontrado')
            db.delete(del_produto)
            db.commit()        
        except SQLAlchemyError as e:
            db.rollback()
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir o produto no banco de dados: {str(e)}")
        else:
            return del_produto
    
    return router