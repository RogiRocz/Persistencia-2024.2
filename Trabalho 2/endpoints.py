from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from db_connect import get_db
from sqlalchemy.exc import SQLAlchemyError
from http import HTTPStatus
import os
import logging as log
import yaml

from crud_produtos import route_produtos, Produtos
from crud_clientes import route_clientes, Clientes
from crud_vendas import route_vendas, Vendas
from crud_fornecedores import route_fornecedores, Fornecedores
from crud_estoque import route_estoque, Estoque

curr_dir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(curr_dir, "config", "config.yaml")

try:
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
        log_config = config['logging']
        path_log_file = os.path.join(curr_dir, 'config', log_config['file'])
        
        os.makedirs(os.path.dirname(path_log_file), exist_ok=True)
        
        file_handler = log.FileHandler(
            filename=path_log_file,
            mode=log_config['filemode'],
            encoding='utf-8'
        )       
        file_handler.setFormatter(log.Formatter(log_config['format']))
        
        log.basicConfig(
            level=log_config['level'],
            handlers=[file_handler, log.StreamHandler()]
        )
        
        logger = log.getLogger(__name__)
        logger.info("Configurações carregadas com sucesso.")
except Exception as e:
    log.basicConfig(level=log.INFO)
    logger = log.getLogger(__name__)
    logger.error(f"Erro ao carregar configurações: {str(e)}")
    raise
else:
    log.getLogger('watchfiles.main').setLevel(log.WARNING)

app = FastAPI()

@app.middleware('http')
async def log_requisicoes(req: Request, prox_chamada):
    logger.info(f'Iniciando a requisição: {req.method} - {req.url}')
    
    try:
        resposta = await prox_chamada(req)
    except Exception as e:
        logger.error(f'Erro durante a requisição: {str(e)}')
        raise
    else:
        logger.info(f'Requisição concluída: {req.method} - {req.url} = Status: {resposta.status_code}')
        return resposta

app.include_router(route_produtos('produtos'))
app.include_router(route_clientes('clientes'))
app.include_router(route_vendas('vendas'))
app.include_router(route_fornecedores('fornecedores'))
app.include_router(route_estoque('estoque'))

@app.get('/quantidade_entidades')
def quantidade_entidades(db: Session = Depends(get_db)):
    resultado = dict()
    logger.info("Iniciando consulta de quantidade de entidades.")

    try:
        query_produtos = db.query(func.count(Produtos.ID_Produto)).scalar()
        query_clientes = db.query(func.count(Clientes.ID_Cliente)).scalar()
        query_vendas = db.query(func.count(Vendas.ID_Venda)).scalar()
        query_fornecedores = db.query(func.count(Fornecedores.ID_Fornecedor)).scalar()
        query_estoque = db.query(func.count(Estoque.ID_Estoque)).scalar()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro ao consultar quantidade de entidades: {str(e)}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Erro ao retornar os dados. Erro: {str(e)}")
    else:
        logger.info("Consulta de quantidade de entidades concluída com sucesso.")
        resultado.update({
            'Produtos': query_produtos,
            'Clientes': query_clientes,
            'Vendas': query_vendas,
            'Fornecedores': query_fornecedores,
            'Estoque': query_estoque
        })
        return resultado

from fastapi import Request  # Adicione esta importação

@app.get('/atributos')
def get_atributos_especificos(entidade: str, request: Request, db: Session = Depends(get_db)):
    logger.info(f"Iniciando consulta de atributos para a entidade: {entidade}")
    
    # Mapeamento de entidades para modelos
    entidade_modelo = {
        "produtos": Produtos,
        "clientes": Clientes,
        "vendas": Vendas,
        "fornecedores": Fornecedores,
        "estoque": Estoque
    }.get(entidade.lower())
    
    # Verifica se a entidade é válida
    if not entidade_modelo:
        logger.error(f"Entidade inválida: {entidade}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Entidade inválida. Entidades válidas: {list(entidade_modelo.keys())}"
        )
    
    try:
        # Cria a query baseada no modelo da entidade
        query = db.query(entidade_modelo)
        
        # Obtém os parâmetros de consulta da requisição
        filtros = request.query_params
        
        # Aplica os filtros passados como parâmetros
        for key, value in filtros.items():
            if key == "entidade":
                continue  # Ignora o parâmetro 'entidade', pois ele já foi processado
            if hasattr(entidade_modelo, key):
                query = query.filter(getattr(entidade_modelo, key) == value)
            else:
                logger.error(f"Atributo '{key}' não existe na entidade '{entidade}'")
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Atributo '{key}' não existe na entidade '{entidade}'."
                )
        
        # Executa a consulta
        resultado = query.all()
        
        # Verifica se há resultados
        if not resultado:
            logger.warning(f"Nenhum resultado encontrado para a entidade '{entidade}' com os filtros fornecidos.")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Nenhum resultado encontrado para a entidade '{entidade}' com os filtros fornecidos."
            )
        
        logger.info(f"Consulta de atributos para a entidade '{entidade}' concluída com sucesso.")
        return resultado
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Erro ao consultar atributos da entidade '{entidade}': {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar atributos da entidade '{entidade}'. Erro: {str(e)}"
        )