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
    path_log_file = os.path.join(curr_dir(), 'config', logging['file'])
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
    except HTTPException as e:
        detail = e.detail if isinstance(e.detail, str) else str(e.detail)
        logger.error(f'Erro durante a requisição: {str(e)} - Detail: {detail}')
        raise
    except Exception as e:
        logger.error(f'Erro durante a requisição: {str(e)}')
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Erro interno do servidor")
    else:
        logger.info(f'Requisição concluída: {req.method} - {req.url} = Status: {resposta.status_code}')
        
        return resposta

app.include_router(router_produtos())
app.include_router(router_clientes())
app.include_router(router_fornecedores())
app.include_router(router_vendas())
app.include_router(router_produtos_fornecidos())
app.include_router(router_estoque())

@app.get('/quantidade_entidades', response_model=dict, description="Retorna a quantidade de entidades por coleção")
async def retorna_qntd_entidades():
    resultado = dict()
    
    try:
        produtos = await db.count(Produtos)
        clientes = await db.count(Clientes)
        fornecedores = await db.count(Fornecedores)
        vendas = await db.count(Vendas)
        pf = await db.count(ProdutosFornecidos)
        estoque = await db.count(Estoque)
    except Exception as e:
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

@app.get('/info_produto/{id_produto}', response_model=dict, description="Retorna informações detalhadas de um produto específico")
async def get_info_produto(id_produto: str):
    try:
        try:
            objectId_produto = ObjectId(id_produto)
        except Exception:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID de produto inválido')
        
        produto = await db.find(Produtos, Produtos.id == objectId_produto)
        if produto is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produto não encontrado')
        
        produto_formatado = [{
            'id': str(p.id),
            'nome': p.nome,
            'valor_unitario': p.valor_unitario,
        } for p in produto]
        
        estocagem = await db.find(Estoque)
        estocagem_filtrada = [item for item in estocagem if item.produto.id == objectId_produto]
        if not estocagem_filtrada:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Estoque não encontrado')        
        estocagem_formatada = [{
            'quantidade': e.quantidade,
            'validade_dias': e.validade_dias
        } for e in estocagem_filtrada]
        
        pf = await db.find(ProdutosFornecidos)
        pf_filtrada = [item for item in pf if item.produto.id == objectId_produto]
        if not pf_filtrada:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Produtos fornecidos não encontrados')
        
        pf_formatada = [{
            'fornecedor': p.fornecedor,
            'quantidade': p.quantidade,
            'custo_unidade': p.custo_unidade
        } for p in pf_filtrada]
        
        resultado = {
            'produto': produto_formatado,
            'estoque': estocagem_formatada,
            'fornecedores': pf_formatada
        }
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao buscar informações do produto. Erro: {str(e)}')
    
    return resultado

@app.get('/clientes_valiosos', response_model=list, description='Mostra o padrão de compras acima da média dos clientes mais valorosos')
async def get_clientes_valiosos():
    try:
        vendas = await db.find(Vendas)
        
        if not vendas:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Nenhuma venda encontrada')
        
        media = sum(venda.valor_total for venda in vendas) / len(vendas)
        
        vendas_acima_media = [venda for venda in vendas if venda.valor_total >= media]
        
        resultado = []
        resultado.append({'média': round(media, 2)})
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
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f'Erro ao buscar clientes valiosos. Erro: {str(e)}')
    
    return resultado

@app.get('/vendas_valores_especificos', response_model=list, description='Recebe ao menos um valor para min ou max para filtrar o valor das vendas. Podendo ordenar asc ou des')
async def get_vendas_valores_especificos(min: float = None, max: float = None, ordem: str = 'asc'):
    try:
        filtros = {}
        ordem_valor = 1 if ordem == 'asc' else -1
        
        if min is None and max is None:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Pelo menos um dos parâmetros 'min' ou 'max' deve ser fornecido. Via query parameters.")
        
        if min is not None:
            filtros["valor_total"] = {"$gte": min}
        if max is not None:
            filtros.setdefault("valor_total", {})["$lte"] = max
        
        if ordem_valor == 1:
            vendas = await db.find(Vendas, filtros, sort=(Vendas.valor_total.asc()))
        else:
            vendas = await db.find(Vendas, filtros, sort=(Vendas.valor_total.desc()))
                
        resultado = [
            {
                'id_venda': str(venda.id),
                'cliente': str(venda.cliente.id),
                'produtos': [
                    {
                    'id_produto': str(item.produto.id), 
                    'nome': item.produto.nome,
                    'valor_unitario': item.produto.valor_unitario,
                    'quantidade': item.quantidade
                    } for item in venda.produtos
                ],
                'valor_total': venda.valor_total
            }
            for venda in vendas
        ]
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Erro ao buscar vendas. Erro: {str(e)}")
        
    return resultado

@app.get('/produtos/buscar', response_model=List[Produtos], description='Busca produtos por parte do nome')
async def buscar_produto_por_nome(buscar: str):
    try:
        if not buscar:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="O parâmetro 'buscar' é obrigatório.")
        
        filtro = {
            "nome": {"$regex": f".*{buscar}.*", "$options": "i"}
        }
        
        produtos = await db.find(Produtos, filtro)
        
        if not produtos:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Nenhum produto encontrado com o nome fornecido.")
    except Exception as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Erro ao buscar produto. Erro: {str(e)}")
    
    return produtos
