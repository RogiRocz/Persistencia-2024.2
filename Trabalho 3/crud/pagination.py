from http import HTTPStatus
from fastapi import HTTPException
from bson import ObjectId
from odmantic import AIOEngine, Model
from pydantic import BaseModel, validator, Field
from typing import Optional, Type

class PaginationParams(BaseModel):
    ultimo_id: Optional[str] = Field(default=None)
    tamanho: int = Field(default=5)
    
    @validator('tamanho')
    def valida_tamanho(cls, valor):
        if valor <= 0:
            raise ValueError('O tamanho da página precisa ser no mínimo 1')
        print(cls, valor)
        
        return valor
    
    async def pagination(self, db: AIOEngine, modelo: Type[Model]):
        try:
            _id = ObjectId(self.ultimo_id) if self.ultimo_id else None
        except ObjectId.InvalidId:
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='ID inválido')
        
        filtros = {'_id': {'$gt': _id}} if _id else {}
        
        resultado = await db.find(modelo, filtros, limit=self.tamanho, sort=modelo.id)
        
        prox_id = str(resultado[-1].id) if resultado else None
        
        total_count = await db.count(modelo)
        total_paginas = (total_count // self.tamanho) + (1 if total_count % self.tamanho != 0 else 0)
        
        if _id:
            count = await db.count(modelo, modelo.id <= _id)
            pagina_atual = (count // self.tamanho) + 1
        else:
            pagina_atual = 1
        
        return {
            'resultado': resultado,
            'prox_id': prox_id,
            'tamanho_pag': self.tamanho,
            'pagina_atual': pagina_atual,
            'total_paginas': total_paginas
        }
