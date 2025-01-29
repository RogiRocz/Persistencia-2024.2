from odmantic import AIOEngine
from motor.motor_asyncio import AsyncIOMotorClient
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
    db = get_db()
    data = get_data(file)
    input = []
    
    for produto in data:
        element = models.Produtos(nome=produto['nome'], valor_unitario=produto['valor_unitario'], codigo_barras=produto['codigo_barras'])
        input.append(element)
    
    await db.save_all(input)

async def create_clientes(file):
    db = get_db()
    data = get_data(file)
    input = []
    
    for cliente in data:
        element = models.Cliente(forma_pagamento=cliente['forma_pagamento'], programa_fidelidade=cliente['programa_fidelidade'])
        input.append(element)
    
    await db.save_all(input)

async def create_fornecedores(file):
    db = get_db()
    data = get_data(file)
    input = []
    
    for fornecedor in data:
        element = models.Fornecedores(nome=fornecedor['nome'], cnpj=fornecedor['cnpj'], endereco=fornecedor['endereco'])
        input.append(element)
    
    await db.save_all(input)

async def create_produtos_fornecidos(file):
    db = get_db()
    data = get_data(file)
    input = []
    
    for pf in data:        
        produto_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == pf['produto'])
        fornecedor_ref = await db.find_one(models.Fornecedores, models.Fornecedores.name == pf['fornecedor'])
        
        element = models.ProdutosFornecidos(produto=produto_ref, fornecedor=fornecedor_ref, quantidade=pf['quantidade'], custo_unidade=pf['custo_unidade'])
        input.append(element)
    
    await db.save_all(input)
    
async def create_estoque(file):
    db = get_db()
    data = get_data(file)
    input = []
    
    for estoque in data:        
        produto_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == estoque['produto'])
                
        element = models.Estoque(produto=produto_ref, quantidade=estoque['quantidade'], validade_dias=estoque['validade_dias'])
        input.append(element)
    
    await db.save_all(input)
    
async def create_vendas(file):
    db = get_db()
    data = get_data(file)
    input = []
    
    for venda in data:        
        produtos_ref = []
        cliente_ref = object
                
        cliente_ref = await db.find_one(models.Cliente, models.Cliente.programa_fidelidade == venda['cliente'])
        for produto in venda['produtos']:
            p_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == produto['codigo_barras'])
            produtos_ref.append(p_ref)
    
    await db.save_all(input)

def popular_db():
    config = get_yaml_config()
    db_populate = config['db-populate']
    folder_path = os.path.join(curr_dir(), db_populate['folder'])
    
    for name in db_populate['data_names']:
        file = os.path.join(folder_path, name) + db_populate['type_files']
        
        try:        
            if name == 'data_produtos':
                create_produtos(file)
            if name == 'data_clientes':
                create_clientes(file)
            if name == 'data_fornecedores':
                create_fornecedores(file)
            if name == 'data_produtos_fornecidos':
                create_produtos_fornecidos(file)
            if name == 'data_estoque':
                create_estoque(file)
            if name == 'data_vendas':
                create_vendas(file)
        except Exception as e:
            print(f'Error ao inserir os dados do arquivo {name}. Erro: {e}')
        