from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import FastAPI

from merchants.config import settings
from merchants.FastapiAdmin import admin
from merchants.version import __version__ as __merchants_version__

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=__merchants_version__,
    description="Universal Payment Processing System",
    debug=True,
)
app.add_middleware(DebugToolbarMiddleware)

admin.mount_to(app)


@app.get("/")
async def root():
    return {"message": "Hello World"}
