from fastapi import FastAPI

from acme_ops_agent.api.routes.chat import router as chat_router
from acme_ops_agent.api.routes.health import router as health_router
from acme_ops_agent.api.routes.me import router as me_router


def create_app() -> FastAPI:
    """
    Create and configure the Acme Operations API application.
    """
    app = FastAPI(
        title="Acme Operations Agent API",
        version="0.1.0",
        description="API boundary for the Acme Operations Agent Application.",
    )

    app.include_router(health_router)
    app.include_router(me_router)
    app.include_router(chat_router)

    return app


app = create_app()