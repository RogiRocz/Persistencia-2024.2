from pydantic import BaseModel, validator

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 10

    @validator('page')
    def validate_page(cls, value):
        if value < 1:
            raise ValueError('A página deve ser maior ou igual a 1.')
        return value

    @validator('page_size')
    def validate_page_size(cls, value):
        if value < 1:
            raise ValueError('O tamanho da página deve ser maior ou igual a 1.')
        return value