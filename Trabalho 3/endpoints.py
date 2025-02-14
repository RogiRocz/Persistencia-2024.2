from typing import List
from fastapi import FastAPI, HTTPException, Request
from crud.crud_router_produtos import router_produtos, Produtos
from crud.crud_router_clientes import router_clientes, Clientes
from crud.crud_router_fornecedores import router_fornecedores, Fornecedores
from crud.crud_router_vendas import router_vendas, Vendas
from crud.crud_router_pf import router_produtos_fornecidos, ProdutosFornecidos
from crud.crud_router_estoque import router_estoque, Estoque
from db_connect import engine as db, curr_dir, get_yaml_config
import os
import logging as log
from http import HTTPStatus
from odmantic import ObjectId

yaml = get_yaml_config()
logging = yaml['logging']

try: 
    path_log_file = os.path.join(curr_dir, 'config', logging['file'])
    os.makedirs(os.path.dirname(path_log_file), exist_ok=True)
    if not os.path.exists(path_log_file):
        with open(path_log_file, 'w') as f:
            pass
    
    file_handler = log.FileHandler(
        filename=path_log_file,
        mode=logging['filemode'],
        encoding='utf-8'
    )
    file_handler.setFormatter(log.Formatter(logging['format']))
    log.basicConfig(level=logging['level'], handlers=[file_handler])
    
    logger = log.getLogger(__name__)
    logger.info('Arquivo de logging carregado com sucesso')
except Exception as e:
    log.basicConfig(level=log.INFO)
    logger = log.getLogger(__name__)
    logger.error(f'Erro ao carregar as informações de logging. Erro: {str(e)}')
else:
    log.getLogger('watchfiles.main').setLevel(log.WARNING)
    if not os.path.exists(path_log_file):
        with open(path_log_file, 'w') as f:
            pass

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

@app.get('/info_produto/{id_produto}', response_model=dict)
async def get_info_produto(id_produto: str):
    try:
        objectId_produto = ObjectId(id_produto)
    except Exception:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID de produto inválido')
    
    produto = await db.find_one(Produtos, Produtos.id == objectId_produto)
    if produto is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
    
    estocagem = await db.find(Estoque, Estoque.produto.id == produto.id)
    if estocagem is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Estoque não encontrados')        
    
    pf = await db.find(ProdutosFornecidos, ProdutosFornecidos.produto.id == produto.id)
    if pf is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produtos fornecidos não encontrados')
    
    resultado = {
        'produto': produto.dict(),
        'estoque': [item.dict() for item in estocagem],
        'fornecedores': [item.dict() for item in pf]
    }
    
    return resultado   

@app.get('/clientes_valiosos', response_model=list, description='Mostra o padrão de compras acima da média dos clientes mais valorosos')
async def get_clientes_valiosos():
    vendas = await db.find(Vendas)
    
    if not vendas:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhuma venda encontrada')
    
    media = sum(venda.valor_total for venda in vendas) / len(vendas)
    
    vendas_acima_media = [venda for venda in vendas if venda.valor_total >= media]
    
    resultado = []
    resultado.append({'média': media})
    for venda in vendas_acima_media:
        cliente = await db.find_one(Clientes, Clientes.id == venda.cliente.id)
        if not cliente:
            continue
        
        produtos_venda = []
        for item in venda.produtos:
            produtos_venda.append({
                'nome': item.produto.nome,
                'valor_unitario': item.produto.valor_unitario,
                'quantidade': item.quantidade
            })
        
        resultado.append({
            'cliente': {
                'id': str(cliente.id),
                'forma_pagamento': cliente.forma_pagamento,
                'programa_fidelidade': cliente.programa_fidelidade
            },
            'produtos': produtos_venda,
            'valor_total': venda.valor_total
        })
    
    return resultado

@app.get('/vendas_valores_especificos', response_model=list, description='Recebe ao menos um valor para min ou max para filtrar o valor das vendas. Podendo ordenar asc ou des')
async def get_vendas_valores_especificos(min: float = None, max: float = None, ordem: str = 'asc'):
    filtros = {}
    ordem_valor = 1 if ordem == 'asc' else -1
    
    if min is None and max is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Pelo menos um dos parâmetros 'min' ou 'max' deve ser fornecido.")
    
    if min is not None:
        filtros["valor_total"] = {"$gte": min}
    if max is not None:
        filtros.setdefault("valor_total", {})["$lte"] = max
    
    vendas = await db.find(Vendas, filtros).sort('valor_total', ordem_valor)
            
    resultado = [
        {
            'id': str(venda.id),
            'cliente': str(venda.cliente.id),
            'produtos': [
                {
                'id_produto': str(item.produto.id), 
                'quantidade': item.quantidade
                } for item in venda.produtos
            ],
            'valor_total': venda.valor_total
        }
        for venda in vendas
    ]
        
    return resultado

@app.get('/produtos/buscar', response_model=List[Produtos])
async def buscar_produto_por_nome(parte_do_nome: str):
    if not parte_do_nome:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="O parâmetro 'parte_do_nome' é obrigatório.")
    
    filtro = {
        "nome": {"$regex": f".*{parte_do_nome}.*", "$options": "i"}
    }
    
    produtos = await db.find(Produtos, filtro)
    
    if not produtos:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Nenhum produto encontrado com o nome fornecido.")
    
    return produtos
