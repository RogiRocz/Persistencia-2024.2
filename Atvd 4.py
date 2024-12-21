from http import HTTPStatus
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import xml.etree.ElementTree as ET

app = FastAPI()

class Livro(BaseModel):
    id: int
    titulo: str
    autor: str
    ano: int
    genero: str

def valida_id(id, tree):
    if id <= 0:
        return False
        
    for livro in tree.findall('livro'):
        if int(livro.attrib['id']) == id:
            return True
    return False

def xml_element_to_json(element):
    return {
        'id': int(element.attrib['id']),
        'titulo': element.find('titulo').text,
        'autor': element.find('autor').text,
        'ano': int(element.find('ano').text),
        'genero': element.find('genero').text
    }

@app.get('/')
def raiz():
    return {'Deu': 'Certo'}

@app.get('/livros')
def retorna_livros():
    livros = ET.parse('livros.xml')
    saida = '{'
    
    testaElem = lambda el : el.text if el is not None else ''
    
    for livro in livros.findall('livro'):
        saida += f'"{livro.get("id")}"' + ':'
        saida += '{'
        saida += '"titulo":' + f'"{testaElem(livro.find("titulo"))}"' + ','
        saida += '"autor":' +  f'"{testaElem(livro.find("autor"))}"' +  ','
        saida += '"ano":' +  f'"{testaElem(livro.find("ano"))}"' +  ','
        saida += '"genero":' +  f'"{testaElem(livro.find("genero"))}"'
        saida += '},'
    saida = saida[:len(saida)-1]
    saida += '}'
    return json.loads(saida)

@app.post('/livros', status_code=HTTPStatus.CREATED, response_model=Livro)
def cria_livro(livro: Livro):
    try:
        tree = ET.parse('livros.xml')
        root = tree.getroot()

        if not valida_id(livro.id, tree):
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        for livro_atual in root.findall('livro'):
            if livro_atual is not None:
                if livro.id == int(livro_atual.get('id')):
                    raise HTTPException(HTTPStatus.CONFLICT, detail="ID já está sendo utilizado")
            raizLivros = ET.Element('livros')
            for livro_atual in root.findall('livro'): raizLivros.append(livro_atual)
            livro_novo = ET.SubElement(raizLivros, 'livro')
            livro_novo.set('id', str(livro.id))
            ET.SubElement(livro_novo, 'titulo').text = livro.titulo
            ET.SubElement(livro_novo, 'autor').text = livro.autor
            ET.SubElement(livro_novo, 'ano').text = str(livro.ano)
            ET.SubElement(livro_novo, 'genero').text = livro.genero
            
            novaTree = ET.ElementTree(raizLivros)
            ET.indent(novaTree, level=1)
            novaTree.write('livros.xml', encoding='unicode')
    except HTTPException as e:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail=e.detail)
    else:
        return livro.model_dump()

@app.put('/livros/{id_livro}',status_code=HTTPStatus.OK, response_model=Livro)
def atualiza_livro(id_livro: int, livro: Livro):
    try:
        tree = ET.parse('livros.xml')
        root = tree.getroot()

        if not valida_id(id_livro, tree):
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='ID inválido')
            
        for livro_atual in root.findall('livro'): 
            if livro_atual is not None:
                if id_livro == int(livro_atual.get('id')):
                    livro_atual.set('id', str(livro.id))
                    livro_atual.find('titulo').text = livro.titulo
                    livro_atual.find('autor').text = livro.autor
                    livro_atual.find('ano').text = str(livro.ano)
                    livro_atual.find('genero').text = livro.genero            
    except HTTPException as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e.detail))
    else:
        tree.write('livros.xml', encoding='unicode')
        return livro.model_dump()

@app.delete('/livros/{id_livro}', status_code=HTTPStatus.OK, response_model=Livro)
def remove_livro(id_livro: int):
    try:
        tree = ET.parse('livros.xml')
        root = tree.getroot()

        if not valida_id(id_livro, tree):
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='ID inválido')

        elementoRemovido = ET.Element('livro')
        
        for livro_atual in root.findall('livro'):
            if livro_atual is not None and id_livro == int(livro_atual.get('id')):
                elementoRemovido = livro_atual
                root.remove(livro_atual)                
    except HTTPException as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=e.detail)
    else:
        tree.write('livros.xml', encoding='unicode')
        return xml_element_to_json(elementoRemovido)