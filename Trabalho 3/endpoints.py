from fastapi import FastAPI
from crud_router_produtos import router_produtos, Produtos
from crud_router_clientes import router_clientes, Clientes
from crud_router_fornecedores import router_fornecedores, Fornecedores
from crud_router_pf import router_produtos_fornecidos, ProdutosFornecidos
from crud_router_estoque import router_estoque, Estoque

app = FastAPI()

app.include_router(router_produtos())
app.include_router(router_clientes())
app.include_router(router_fornecedores())
app.include_router(router_produtos_fornecidos())
app.include_router(router_estoque())