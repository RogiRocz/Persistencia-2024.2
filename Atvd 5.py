import logging as log
import yaml
import json

try:
  with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

    log.basicConfig(filename=config['logging']['file'], format=config['logging']['format'], level=config['logging']['level'], filemode='w')
except Exception as e:
  print('Erro ao ler o arquivo de configuração: ', e)
else:
  log.info('Arquivo de configuração lido com sucesso.')

try:
  with open(config['data']['file'], 'r') as dataJson:
    data = json.load(dataJson)
    capitais = data['capitais']
    
    for cidade in capitais:
      warming = False
      for chave, valor in cidade.items():
        yaml_json_format_type = config['formatter_json'][f'{chave}']
        yaml_json_format_type  = 'str' if yaml_json_format_type == 'string' else yaml_json_format_type
        if yaml_json_format_type != type(valor).__name__:
          log.warning('Erro no registro: ' + str(cidade) + ' - Dado inválido: ' +  str(chave))
          warming = True
      
      if warming == False: log.info('Processando registro: ' + str(cidade))
except Exception as e:
  print('Erro ao ler o arquivo JSON.', e)
  log.error('Erro ao ler o arquivo JSON.')