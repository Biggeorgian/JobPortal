import os
from app import application

if __name__ == '__main__':
    os.environ['WERKZEUG_LOG_NO_ANSI'] = 'true'

    application.run(debug=True)