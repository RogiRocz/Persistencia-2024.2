from bs4 import BeautifulSoup as BS
import requests as req
import pytesseract as pyt
from PIL import Image
import shutil

# Configurando o path do tesseract
pyt.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

siteUrl = 'https://animesdigital.org'

res = req.request('get', siteUrl)
doc = BS(res.content, 'html.parser')
title = doc.title.string

for link in doc.find_all('a'):
    print(link.get('href'))

urlImage = 'https://www.portaldecamaqua.com.br/images/usuario/1716038331193.png'

res = req.get(urlImage, stream=True)

with open('imagemSaida.png', 'wb') as imgOutput:
    shutil.copyfileobj(res.raw, imgOutput)

image = Image.open('./imagemSaida.png')
text = pyt.image_to_string(image)

with open('textoImg.txt', 'w') as file:
    print(text, file=file)