import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'a4u-webapp'))

from app import app, init_db

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
