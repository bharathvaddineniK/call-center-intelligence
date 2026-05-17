from src.database.session import init_db
from src.ui.app import app

if __name__ == "__main__":
    init_db()
    app.launch()