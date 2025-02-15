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
        element = models.Produtos(nome=produto['nome'], valor_unitario=produto['valor_unitario'], codigo_barras=produto['codigo_barras'])
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
        if produto_ref is None:
            continue
        if pf['custo_unidade'] is None:
            continue
        
        fornecedor_ref = await db.find_one(models.Fornecedores, models.Fornecedores.cnpj == pf['fornecedor'])
        if not fornecedor_ref:
            continue
        
        element = models.ProdutosFornecidos(produto=produto_ref, fornecedor=fornecedor_ref, quantidade=pf['quantidade'], custo_unidade=pf['custo_unidade'])
        input.append(element)
    
    await db.save_all(input)
    
async def create_estoque(file):
    db = engine
    data = get_data(file)
    input = []
    
    for estoque in data:        
        produto_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == estoque['produto'])
        if produto_ref is None:
            print(f"create_estoque - Produto não encontrado: {estoque['produto']}")
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
        cliente_ref = None
        
        if venda['cliente'] is not None and venda['cliente'] != '':
            cliente_ref = await db.find_one(models.Clientes, models.Clientes.programa_fidelidade == venda['cliente'])
            if cliente_ref.forma_pagamento != venda['forma_pagamento']:
                cliente_ref.forma_pagamento = venda['forma_pagamento']
        else:
            cliente_ref = models.Clientes(programa_fidelidade=None, forma_pagamento=venda['forma_pagamento'])
        for produto in venda['produtos']:
            p_ref = await db.find_one(models.Produtos, models.Produtos.codigo_barras == produto['produto'])
            if p_ref is None:
                print(f"create_vendas - Produto não encontrado: {produto['produto']}")
                continue
            
            item_venda = models.ItemVenda(produto=p_ref, quantidade=produto['quantidade'])
            produtos_ref.append(item_venda)
            
        valor_t = 0
        for item in produtos_ref:
            produto = item.produto
            valor_un = produto.valor_unitario
            qntd = item.quantidade
            valor_t += valor_un * qntd
        
        element = models.Vendas(cliente=cliente_ref, produtos=produtos_ref, valor_total=valor_t)
        input.append(element)
            
    await db.save_all(input)
    
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