from pydantic import BaseModel, field_validator

class PaginationParams(BaseModel):
    ultimo_id: str = None
    tamanho: int = 5
    
    @field_validator(tamanho)
    def valida_tamanho(cls, valor):
        if valor <= 0:
            raise ValueError('O tamanho da página precisa ser no mínimo 1')