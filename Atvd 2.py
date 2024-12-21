import os
import zipfile as zip

# Lendo o diretorio
path = './Textos/'

# Criando arquivo de resultado
open('./resultado.txt', 'w')
for files in os.scandir('./Textos'):
  with open(path + files.name, 'r') as file:
    # Contando a qntd de palavras e letras
    countWords = 0
    countLetters = 0
    for line in file:
      if(not line.isspace()):
        for word in line.split():
          countWords += 1
          for letters in word:
            countLetters += 1
    # Imprindo resultado
    with open('resultado.txt', 'a') as file:
      print(f'Arquivo: {files.name} - Palavras: {countWords} - Letras: {countLetters} \n', file=file)

# Criando arquivo zipado
with zip.ZipFile('saida.zip', 'w') as zipper:
    zipper.write('resultado.txt')