# Render 배포용 메인 앱 파일
from complete_game import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)