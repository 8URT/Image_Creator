from app import create_app
import os

app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=3033)
