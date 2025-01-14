from flask import Flask, jsonify
from flask_cors import CORS
import redis
import requests
import os
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

redis_host = os.getenv('REDIS_HOST', 'redis')
redis_port = os.getenv('REDIS_PORT', '6379')
if redis_port.startswith('tcp://'):
    redis_host = redis_port.split('://')[1].split(':')[0]
    redis_port = '6379'

# Redis connection with error handling
def get_redis_client():
    try:
        client = redis.Redis(
            host=redis_host,
            port=int(redis_port),
            db=0,
            decode_responses=True,
            socket_timeout=5  # Add timeout
        )
        client.ping()  # Test connection
        return client
    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

redis_client = get_redis_client()

TODO_SERVICE_URL = os.getenv('TODO_SERVICE_URL', 'http://todo-service:5000')

def get_todos():
    try:
        logger.info(f"Fetching todos from {TODO_SERVICE_URL}")
        response = requests.get(f"{TODO_SERVICE_URL}/todos", timeout=5)
        response.raise_for_status()
        todos = response.json()
        logger.info(f"Successfully fetched {len(todos)} todos")
        return todos
    except requests.RequestException as e:
        logger.error(f"Error fetching todos: {e}")
        return []

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        # Attempt to get cached stats
        if redis_client:
            try:
                cached_stats = redis_client.get('todo_stats')
                if cached_stats:
                    logger.info("Returning cached stats")
                    return jsonify(json.loads(cached_stats))
            except redis.RedisError as e:
                logger.error(f"Redis error: {e}")
        
        # If no cache or redis error, compute new stats
        todos = get_todos()
        if not todos:
            logger.warning("No todos found or error fetching todos")
            return jsonify({
                'error': 'Unable to fetch todos',
                'total_todos': 0,
                'completed_todos': 0,
                'completion_rate': 0,
                'todos_created_today': 0
            }), 500

        total_todos = len(todos)
        completed_todos = len([t for t in todos if t['completed']])
        completion_rate = (completed_todos / total_todos * 100) if total_todos > 0 else 0

        today = datetime.utcnow().date()
        today_todos = len([
            t for t in todos 
            if datetime.fromisoformat(t['created_at'].replace('Z', '+00:00')).date() == today
        ])

        stats = {
            'total_todos': total_todos,
            'completed_todos': completed_todos,
            'completion_rate': round(completion_rate, 2),
            'todos_created_today': today_todos
        }

        # Cache the new stats with shorter TTL
        if redis_client:
            try:
                redis_client.setex('todo_stats', 60, json.dumps(stats))  # Reduced to 60 seconds
                logger.info("Successfully cached new stats")
            except redis.RedisError as e:
                logger.error(f"Failed to cache stats: {e}")

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Unexpected error in get_stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/invalidate-cache', methods=['POST'])
def invalidate_cache():
    try:
        if redis_client:
            redis_client.delete('todo_stats')
            logger.info("Successfully invalidated stats cache")
            return jsonify({'status': 'success'})
        return jsonify({'status': 'redis not available'}), 503
    except redis.RedisError as e:
        logger.error(f"Failed to invalidate cache: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    health_status = {
        'status': 'healthy',
        'redis_connected': bool(redis_client),
        'todo_service': 'unknown'
    }
    
    try:
        requests.get(f"{TODO_SERVICE_URL}/todos", timeout=5)
        health_status['todo_service'] = 'connected'
    except requests.RequestException:
        health_status['todo_service'] = 'disconnected'
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)