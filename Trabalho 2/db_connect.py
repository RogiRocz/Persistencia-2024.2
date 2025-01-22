from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, Session
import db_models
import yaml
import json
import os
import logging as log
from sqlalchemy import event
import psycopg2 as ps

def get_config():
    # Lembra de colocar os logs
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(curr_dir, "config", "config.yaml")
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
        return config    

# Configurando o log
def configura_logging():
    config = get_config()
    curr_dir = os.path.abspath(os.path.dirname(__file__))
    logfile_path = os.path.join(curr_dir, "config", config['logging']['file'])
    if os.path.exists(logfile_path) == False:
        try:
            open(logfile_path, mode='w').close()
        except FileExistsError as e:
            print(f'Erro a criar o arquivo de log. Erro: {e}')
            raise
    log_config = config['logging']
    log.basicConfig(filename=logfile_path, level=log_config['level'], format=log_config['format'], filemode=log_config['filemode'])
    log.info('Logging configurado com sucesso')

# Conectando ao banco de dados
config = get_config()
db_connection = config['db_connection']
dbname, host, port, user, password = db_connection["database"], db_connection["host"], db_connection["port"], db_connection["user"], db_connection["password"]

url_conn = URL.create("postgresql+psycopg2", username = user, password = password, host = host, database = dbname, query={'client_encoding': 'utf8'})
engine = create_engine(url=url_conn)

db_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def cria_tabelas():
    log.info('Criando as tabelas')
    try:
        db_models.Base.metadata.drop_all(bind=engine)
        db_models.Base.metadata.create_all(bind=engine)
    except Exception as e:
        log.critical('Erro a criar todas as tabelas')
        print(f'Erro a criar todas as tabelas. Erro: {e}')
        raise
    else:
        log.info('Tabelas criadas com sucesso')
        
    log.info('Inserindo dados iniciais')
    with db_session() as db:
        inserir_dados(db)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
        
def existe_elemento(db, model, pk):
    try:
        return db.get(model, pk) is not None
    except Exception as e:
        log.error(f"Erro ao validar existência do elemento: {e}")
        return False
    
def create_produtos(db, file_json):
    with open(file_json, "r", encoding='utf-8') as file:
        data = file.read()
        data = json.loads(data)
        for produto in data:
            if not existe_elemento(db, db_models.Produtos, produto['ID_Produto']):
                db.add(db_models.Produtos(ID_Produto=produto["ID_Produto"], nome=produto["Nome"], valor_unitario=produto["Valor_Unitario"]))

def create_clientes(db, file_json):
    with open(file_json, "r", encoding='utf-8') as file:
        data = file.read()
        data = json.loads(data)
        for cliente in data:
            if not existe_elemento(db, db_models.Clientes, cliente['ID_Cliente']):
                db.add(db_models.Clientes(ID_Cliente=cliente["ID_Cliente"], forma_pagamento=cliente['Forma_Pagamento'], programa_fidelidade=cliente["Programa_Fidelidade"]))

def create_fornecedores(db, file_json):
    with open(file_json, "r", encoding='utf-8') as file:
        data = file.read()
        data = json.loads(data)
        for fornecedor in data:
            if not existe_elemento(db, db_models.Fornecedores, fornecedor['ID_Fornecedor']):
                db.add(db_models.Fornecedores(ID_Fornecedor=fornecedor["ID_Fornecedor"], nome=fornecedor["Nome"], ID_Produto=fornecedor["ID_Produto"], quantidade=fornecedor["Quantidade"], valor_unitario=fornecedor["Valor_Unitario"]))

def create_estoque(db, file_json):
    with open(file_json, "r", encoding='utf-8') as file:
        data = file.read()
        data = json.loads(data)
        for estoque in data:
            if not existe_elemento(db, db_models.Estoque, estoque['ID_Estoque']):
                db.add(db_models.Estoque(ID_Estoque=estoque["ID_Estoque"], ID_Fornecedor=estoque["ID_Fornecedor"], ID_Produto=estoque["ID_Produto"], quantidade=estoque["Quantidade"], categoria=estoque["Categoria"], validade_dias=estoque["Validade_Dias"]))

def create_vendas(db, file_json):
    with open(file_json, "r", encoding='utf-8') as file:
        data = file.read()
        data = json.loads(data)
        for venda in data:
            if not existe_elemento(db, db_models.Vendas, venda['ID_Venda']):
                db.add(db_models.Vendas(ID_Venda=venda["ID_Venda"], ID_Cliente=venda["ID_Cliente"], ID_Produto=venda["ID_Produto"], quantidade=venda["Quantidade"], valor_total=venda["Valor_Total"]))
            

def inserir_dados(db):
    config = get_config()
    files_data_inserted = config['files_data_inserted']
    for file in files_data_inserted:
        curr_dir = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(curr_dir, './data_json/', file)
        try:
            if "data_produtos.json" in file:
                create_produtos(db, file_path)
            elif "data_clientes.json" in file:
                create_clientes(db, file_path)
            elif "data_fornecedores.json" in file:
                create_fornecedores(db, file_path)
            elif "data_estoque.json" in file:
                create_estoque(db, file_path)
            elif "data_vendas.json" in file:
                create_vendas(db, file_path)
            db.commit()
            log.info(f"Dados inseridos do arquivo: {file_path}")
        except Exception as e:
            log.error(f"Erro ao ler dados do arquivo {file_path}: {e}")
            db.rollback()
        
if __name__ == '__main__':
    configura_logging()
    cria_tabelas()