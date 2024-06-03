import time
from flask import Flask, jsonify
from redis import Redis
from rq import Queue
from task import process_question
from random import randint
from flask_caching import Cache
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

# Connect to Redis for task queue management
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', 6379)
redis_conn = Redis(host=redis_host, port=redis_port)
q = Queue(connection=redis_conn)

@app.route('/')
def index():
    random = randint(1, 1000)
    return f'<h1> The number is : {random} </h1>'

@app.route('/scorecard/<question>', methods=['GET'])
def chatbot(question):
    try:
        job = q.enqueue(process_question, question)
        # Wait for job to finish and get the result
        result = job.result

        # Check if result is None
        if result is not None:
            return jsonify(result['output'])
        else:
            return jsonify({"error": "Job result is None"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.getenv("PORT"), debug=True)
