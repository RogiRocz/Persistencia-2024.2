import pandas as pd

# Parte 1 atvd
arq_csv = pd.read_csv('vendas.csv')

# Parte 2 atvd
arq_csv['Total_Venda'] = 0
arq_csv = arq_csv.sort_values(by='Produto')
colunas = ["Data" ,"Produto", "Quantidade", "Preco_Unitario", 'Total_Venda']
global data, produto, qntd, preco_un, total_venda
global total_vendas, vendas_janeiro
total_vendas = []
vendas_janeiro = []

totalVenda = lambda q, p: q * p

for prod in arq_csv.values:
    data = prod[0]
    produto = prod[1]
    qntd = prod[2]
    preco_un = prod[3]
    prod[4] = totalVenda(qntd, preco_un)
    total_vendas.append(prod)
    
# Parte 3 atvd
for prod in arq_csv.values:
    data = prod[0]
    d, m, a = data.split('/')
    if(m == '01' and a == '2023'):
        qntd = prod[2]
        preco_un = prod[3]
        prod[4] = totalVenda(qntd, preco_un)
        vendas_janeiro.append(prod)
        
df = pd.DataFrame(vendas_janeiro, columns=colunas)

# Parte 4 atvd
df.to_csv("vendas_janeiro.csv",index=False)
pd.DataFrame().to_excel('total_vendas_produto.xlsx')

j = 0
i = 0
indices = []
ultimoProd = ''
while (i < len(total_vendas) - 1):
    prod_atual = total_vendas[i][1]
    prox_prod = total_vendas[i+1][1]
    if(prod_atual != prox_prod):
        with pd.ExcelWriter('total_vendas_produto.xlsx', engine='openpyxl', mode='a') as writer:
            novoDf = pd.DataFrame(total_vendas[j:i], columns=colunas)
            novoDf.to_excel(writer, sheet_name=f'{prod_atual}')
        indices.append([j, i])
        j = i + 1
        ultimoProd = prox_prod
    i = i + 1
indices.append([j, i])
print(indices)
with pd.ExcelWriter('total_vendas_produto.xlsx', engine='openpyxl', mode='a') as writer:
    novoDf = pd.DataFrame(total_vendas[j:i], columns=colunas)
    novoDf.to_excel(writer, sheet_name=f'{ultimoProd}')