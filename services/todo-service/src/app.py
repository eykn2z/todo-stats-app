from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@postgres:5432/todos')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@app.route('/todos', methods=['GET'])
def get_todos():
    todos = Todo.query.all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'completed': t.completed,
        'created_at': t.created_at.isoformat(),
        'updated_at': t.updated_at.isoformat()
    } for t in todos])

@app.route('/todos', methods=['POST'])
def create_todo():
    data = request.get_json()
    todo = Todo(title=data['title'])
    db.session.add(todo)
    db.session.commit()
    return jsonify({
        'id': todo.id,
        'title': todo.title,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'updated_at': todo.updated_at.isoformat()
    })

@app.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    todo.completed = data.get('completed', todo.completed)
    todo.title = data.get('title', todo.title)
    db.session.commit()
    return jsonify({
        'id': todo.id,
        'title': todo.title,
        'completed': todo.completed,
        'created_at': todo.created_at.isoformat(),
        'updated_at': todo.updated_at.isoformat()
    })

@app.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
