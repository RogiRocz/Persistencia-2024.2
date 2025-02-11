from typing import List
from fastapi import FastAPI, HTTPException, Request
from .crud.crud_router_produtos import router_produtos, Produtos, ProdutoPy
from .crud.crud_router_clientes import router_clientes, Clientes, ClientesPy
from .crud.crud_router_fornecedores import router_fornecedores, Fornecedores, FornecedoresPy
from .crud.crud_router_vendas import router_vendas, Vendas, ItemVenda, VendasPy, ItemVendaPy
from .crud.crud_router_pf import router_produtos_fornecidos, ProdutosFornecidos, ProdutosFornecidosPy
from .crud.crud_router_estoque import router_estoque, Estoque, EstoquePy
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

@app.get('/info_produto/{id_produto}', response_model=dict)
async def get_info_produto(id_produto: str):
    try:
        object_id = ObjectId(id_produto)
    except Exception:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID de produto inválido')
    
    prod = await db.find_one(Produtos, Produtos.id == object_id)
    if prod is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
    
    estocagem = await db.find(Estoque, Estoque.produto == prod)
    
    pf = await db.find(ProdutosFornecidos, ProdutosFornecidos.produto == prod)
    
    resultado = {
        'produto': {
            'id': str(prod.id),
            'nome': prod.nome,
            'codigo_barras': prod.codigo_barras,
            'valor_unitario': prod.valor_unitario
        },
        'estoque': [
            {
                'quantidade': item.quantidade,
                'validade_dias': item.validade_dias
            } for item in estocagem
        ],
        'fornecedores': [
            {
                'nome': item.fornecedor.nome,
                'cnpj': item.fornecedor.cnpj,
                'endereco': item.fornecedor.endereco,
                'quantidade': item.quantidade,
                'custo_unidade': item.custo_unidade
            } for item in pf
        ]
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

@app.get('/vendas_valores_especificos', response_model=list, description='Recebe ao menos um valor para min ou max para filtrar o valor das vendas')
async def get_vendas_valores_especificos(min: float = None, max: float = None):
    resultado = []
    
    if min is None and max is None:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Pelo menos um dos parâmetros 'min' ou 'max' deve ser fornecido.")
    
    if min is None and max:
        vendas = await db.find(Vendas, Vendas.valor_total <= max)
        for venda in vendas:
            resultado.append({
                    'id': str(venda.id),
                    'cliente': str(venda.cliente.id),
                    'produtos': [{
                        'id_produto': str(item.produto.id),
                        'quantidade': item.quantidade
                    } for item in venda.produtos],
                    'valor_total': venda.valor_total

            })
    
    if max is None and min:
        vendas = await db.find(Vendas, Vendas.valor_total >= min)
        for venda in vendas:
            resultado.append({
                    'id': str(venda.id),
                    'cliente': str(venda.cliente.id),
                    'produtos': [{
                        'id_produto': str(item.produto.id),
                        'quantidade': item.quantidade
                    } for item in venda.produtos],
                    'valor_total': venda.valor_total

            })
            
    if min and max:
        vendas = await db.find(Vendas, Vendas.valor_total >= min & Vendas.valor_total <= max)
        for venda in vendas:
            resultado.append({
                    'id': str(venda.id),
                    'cliente': str(venda.cliente.id),
                    'produtos': [{
                        'id_produto': str(item.produto.id),
                        'quantidade': item.quantidade
                    } for item in venda.produtos],
                    'valor_total': venda.valor_total

            })
        
    
    return resultado

@app.get('/produtos/buscar', response_model=List[ProdutoPy])
async def buscar_produto_por_nome(parte_do_nome: str):
    if not parte_do_nome:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="O parâmetro 'parte_do_nome' é obrigatório.")
    
    filtro = {
        "nome": {"$regex": f".*{parte_do_nome}.*", "$options": "i"}
    }
    
    produtos = await db.find(Produtos, filtro)
    
    if not produtos:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Nenhum produto encontrado com o nome fornecido.")
    
    response = [
        ProdutoPy(
            id=str(produto.id),
            nome=produto.nome,
            codigo_barras=produto.codigo_barras,
            valor_unitario=produto.valor_unitario
        ) for produto in produtos
    ]
    
    return response