from fastapi import FastAPI, HTTPException, Request
from crud_router_produtos import router_produtos, Produtos
from crud_router_clientes import router_clientes, Clientes
from crud_router_fornecedores import router_fornecedores, Fornecedores
from crud_router_vendas import router_vendas, Vendas, ItemVenda
from crud_router_pf import router_produtos_fornecidos, ProdutosFornecidos
from crud_router_estoque import router_estoque, Estoque
from db_connect import engine as db, curr_dir, get_yaml_config
import os
import logging as log
from http import HTTPStatus

yaml = get_yaml_config()
logging = yaml['logging']

try: 
    path_log_file = os.path.join(curr_dir, 'config', logging['file'])
    os.makedirs(os.path.dirname(path_log_file), exist_ok=True)
    
    file_handler = log.FileHandler(
        filename=path_log_file,
        mode=logging['filemode'],
        encoding='utf-8'
    )
    file_handler.setFormatter(log.Formatter(logging['format']))
    log.basicConfig(level=logging['level'], handlers=[file_handler, log.StreamHandler()])
    
    logger = log.getLogger(__name__)
    logger.info('Arquivo de logging carregado com sucesso')
except Exception as e:
    log.basicConfig(level=log.INFO)
    logger = log.getLogger(__name__)
    logger.error(f'Erro ao carregar as informações de logging. Erro: {str(e)}')
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

app.include_router(router_produtos())
app.include_router(router_clientes())
app.include_router(router_fornecedores())
app.include_router(router_vendas())
app.include_router(router_produtos_fornecidos())
app.include_router(router_estoque())

@app.get('/quantidade_entidades', response_model=dict)
async def retorna_qntd_entidades():
    resultado = dict()
    logger.info('Consultando a quatidade de entidade por coleção')
    
    try:
        produtos = await db.count(Produtos)
        clientes = await db.count(Clientes)
        fornecedores = await db.count(Fornecedores)
        vendas = await db.count(Vendas)
        pf = await db.count(ProdutosFornecidos)
        estoque = await db.count(Estoque)
    except Exception as e:
        logger.error(f'Erro ao calcular a quantidade de entidades. Erro: {str(e)}')
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao calcular a quantidade de entidades. Erro: {str(e)}')
    else:
        resultado.update({
            'Produtos': produtos,
            'Clientes': clientes,
            'Fornecedores': fornecedores,
            'Vendas': vendas,
            'Produtos Fornecidos': pf,
            'Estoque': estoque
        })
        
        return resultado