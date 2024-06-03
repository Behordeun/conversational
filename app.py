import time
from flask import Flask, jsonify, request
from redis import Redis
from task import process_question
from random import randint
from flask_caching import Cache
import os
from dotenv import load_dotenv
from celery import Celery
from celery.result import AsyncResult

load_dotenv()

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# Celery configuration
app.config['CELERY_BROKER_URL'] = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0"
app.config['CELERY_RESULT_BACKEND'] = f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0"
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@app.route('/')
def index():
    random = randint(1, 1000)
    return f'<h1>The number is: {random}</h1>'

@app.route('/scorecard/<question>', methods=['GET'])
def chatbot(question):
    try:
        # Enqueue task and wait for it to complete
        task = process_question.apply_async(args=[question])
        while not task.ready():
            time.sleep(1)
        result = task.get()

        # Check if result is None
        if result is not None:
            return jsonify({'output': result}), 200
        else:
            return jsonify({"error": "Task result is None"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/result/<task_id>', methods=['GET'])
def get_result(task_id):
    try:
        task = AsyncResult(task_id, app=celery)
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'status': 'Pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'result': task.result
            }
        else:
            response = {
                'state': task.state,
                'status': str(task.info)
            }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5050)), debug=True)
