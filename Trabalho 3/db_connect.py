from motor.motor_asyncio import AsyncIOMotorClient
from odmantic import AIOEngine
import asyncio
import models
import yaml
import json
import os

uri = 'mongodb://localhost:27017/'
client = AsyncIOMotorClient(uri)
database = 'Trabalho_03'
engine = AIOEngine(client=client, database=database)

def get_db():
    session = engine.session()
    try:
        yield session
    finally:
        session.end()

def curr_dir():
    return os.path.abspath(os.path.dirname(__file__))

def get_yaml_config():
    config_path = os.path.join(curr_dir(), 'config', 'config.yaml')
    with open(config_path, 'r') as yaml_file:
        return yaml.safe_load(yaml_file)

def get_data(file):
    with open(file, mode='r', encoding='utf-8') as file:
        data = file.read()
        return json.loads(data)
    
    
async def create_produtos(file):
    db = engine
    data = get_data(file)
    input = []
    
    for produto in data:
        element = models.Produtos(nome=produto['nome'], valor_unitario=str(produto['valor_unitario']), codigo_barras=produto['codigo_barras'])
        input.append(element)
    
    await db.save_all(input)

async def create_clientes(file):
    db = engine
    data = get_data(file)
    input = []
    
    for cliente in data:
        element = models.Clientes(forma_pagamento=cliente['forma_pagamento'], programa_fidelidade=cliente['programa_fidelidade'])
        input.append(element)
    
    await db.save_all(input)

async def create_fornecedores(file):
    db = engine
    data = get_data(file)
    input = []
    
    for fornecedor in data:
        element = models.Fornecedores(nome=fornecedor['nome'], cnpj=fornecedor['cnpj'], endereco=fornecedor['endereco'])
        input.append(element)
    
    await db.save_all(input)

async def create_produtos_fornecidos(file):
    db = engine
    data = get_data(file)
    input = []
    
    for pf in data:        
        produto_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == pf['produto'])
        if not produto_ref:
            print(f'create_produtos_fornecidos - Produto não encontrado: {pf['produto']}')
            continue
        if not pf['custo_unidade']:
            print(f'create_produtos_fornecidos - O custo_unidade é nulo: {pf['produto']}')
            continue
        fornecedor_ref = await db.find_one(models.Fornecedores, models.Fornecedores.cnpj == pf['fornecedor'])
        if not fornecedor_ref:
            print(f'create_produtos_fornecidos - Fornecedor não encontrado: {pf['fornecedor']}')
            continue
        
        if produto_ref and fornecedor_ref and pf['custo_unidade']:
            element = models.ProdutosFornecidos(produto=produto_ref, fornecedor=fornecedor_ref, quantidade=pf['quantidade'], custo_unidade=str(pf['custo_unidade']))
            input.append(element)
    
    await db.save_all(input)
    
async def create_estoque(file):
    db = engine
    data = get_data(file)
    input = []
    
    for estoque in data:        
        produto_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == estoque['produto'])
        if not produto_ref:
            print(f'create_estoque - Produto não encontrado: {estoque['produto']}')
            continue
        else:
            element = models.Estoque(produto=produto_ref, quantidade=estoque['quantidade'], validade_dias=estoque['validade_dias'])
            input.append(element)
    
    await db.save_all(input)
    
async def create_vendas(file):
    db = engine
    data = get_data(file)
    input = []
    
    for venda in data:
        produtos_ref = []
        cliente_ref = object
                
        cliente_ref = await db.find_one(models.Clientes, models.Clientes.programa_fidelidade == venda['cliente'])
        for produto in venda['produtos']:
            p_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == produto['produto'])
            if not p_ref:
                print(f'create_vendas - Produto não encontrado: {produto['produto']}')
                continue
            elif not p_ref.valor_unitario:
                print(f'create_vendas - O valor_unitario é nulo: {produto['produto']}')
                continue
            else:
                item_venda = models.ItemVenda(produto=p_ref, quantidade=produto['quantidade'])
                produtos_ref.append(item_venda)
        
        if cliente_ref:
            element = models.Vendas(cliente=cliente_ref, produtos=produtos_ref)
            element.valor_total = element.calcular_valor_total()
            input.append(element)
            await db.save_all(input)
        else:
            print(f'create_vendas - Clientes não encontrado: {cliente_ref}')
    

async def popular_db():
    config = get_yaml_config()
    db_populate = config['db-populate']
    folder_path = os.path.join(curr_dir(), db_populate['folder'])
    
    for name in db_populate['data_names']:
        file = os.path.join(folder_path, name) + db_populate['type_files']
        
        try:        
            if name == 'data_produtos':
                await create_produtos(file)
            if name == 'data_clientes':
                await create_clientes(file)
            if name == 'data_fornecedores':
                await create_fornecedores(file)
            if name == 'data_produtos_fornecidos':
                await create_produtos_fornecidos(file)
            if name == 'data_estoque':
                await create_estoque(file)
            if name == 'data_vendas':
                await create_vendas(file)
        except Exception as e:
            print(f'Error ao inserir os dados do arquivo {name}. Erro: {str(e)}')

if __name__ == '__main__':
    asyncio.run(popular_db())