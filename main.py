from config import Config
from app import create_app, setup_database, initialize_mimetypes

app = create_app(Config)
setup_database(app)
initialize_mimetypes(app)

if __name__ == '__main__':
  app.run(debug=app.config['DEBUG'])