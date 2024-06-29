from fastapi import APIRouter

merchants = APIRouter()


# Acá irán las URL para los callbacks
# Dejar así hasta llegar a esa etapa
@merchants.get("/")
async def default_root():
    return {"Hello": "World"}
