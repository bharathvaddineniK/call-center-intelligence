import os

from src.database.session import init_db
from src.ui.app import APP_CSS, app, theme


def get_server_port() -> int | None:
    """Return an explicit Gradio port only when the environment requests one."""
    port = os.getenv("GRADIO_SERVER_PORT")
    return int(port) if port else None


if __name__ == "__main__":
    init_db()
    app.launch(
        server_name="0.0.0.0",
        server_port=get_server_port(),
        theme=theme,
        css=APP_CSS,
    )
