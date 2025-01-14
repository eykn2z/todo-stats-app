import React, { useState, useEffect } from 'react';
import axios from 'axios';

declare global {
  interface Window {
    ENV: {
      REACT_APP_TODO_SERVICE_URL: string;
      REACT_APP_STATS_SERVICE_URL: string;
    };
  }
}

const TODO_SERVICE_URL = window.ENV.REACT_APP_TODO_SERVICE_URL || process.env.REACT_APP_TODO_SERVICE_URL || 'http://127.0.0.1:30001';
const STATS_SERVICE_URL = window.ENV.REACT_APP_STATS_SERVICE_URL || process.env.REACT_APP_STATS_SERVICE_URL || 'http://127.0.0.1:30002';

interface Todo {
  id: number;
  title: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

interface Stats {
  total_todos: number;
  completed_todos: number;
  completion_rate: number;
  todos_created_today: number;
}

function App() {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [newTodo, setNewTodo] = useState('');
  const [error, setError] = useState<string | null>(null);

  // キャッシュ無効化関数の追加
  const invalidateStatsCache = async () => {
    try {
      if (!STATS_SERVICE_URL) throw new Error('Stats service URL not configured');
      await axios.post(`${STATS_SERVICE_URL}/invalidate-cache`);
      await fetchStats(); // キャッシュ無効化後に即時データ取得
    } catch (error) {
      console.error('Error invalidating stats cache:', error);
      // キャッシュ無効化に失敗してもstatsは更新を試みる
      await fetchStats();
    }
  };

  useEffect(() => {
    fetchTodos();
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchTodos = async () => {
    try {
      if (!TODO_SERVICE_URL) throw new Error('Todo service URL not configured');
      const response = await axios.get<Todo[]>(`${TODO_SERVICE_URL}/todos`);
      setTodos(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching todos:', error);
      setError('Failed to fetch todos');
    }
  };

  const fetchStats = async () => {
    try {
      if (!STATS_SERVICE_URL) throw new Error('Stats service URL not configured');
      const response = await axios.get<Stats>(`${STATS_SERVICE_URL}/stats`);
      setStats(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching stats:', error);
      setError('Failed to fetch stats');
    }
  };

  const addTodo = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (!TODO_SERVICE_URL) throw new Error('Todo service URL not configured');
      await axios.post(`${TODO_SERVICE_URL}/todos`, { title: newTodo });
      setNewTodo('');
      await fetchTodos();
      await invalidateStatsCache(); // 追加後にキャッシュを無効化
      setError(null);
    } catch (error) {
      console.error('Error adding todo:', error);
      setError('Failed to add todo');
    }
  };

  const toggleTodo = async (todo: Todo) => {
    try {
      if (!TODO_SERVICE_URL) throw new Error('Todo service URL not configured');
      await axios.put(`${TODO_SERVICE_URL}/todos/${todo.id}`, {
        ...todo,
        completed: !todo.completed
      });
      await fetchTodos();
      await invalidateStatsCache(); // 更新後にキャッシュを無効化
      setError(null);
    } catch (error) {
      console.error('Error updating todo:', error);
      setError('Failed to update todo');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8 text-center">Todo App with Stats</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
          {error}
        </div>
      )}
      
      {stats && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Statistics</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <p className="text-sm text-blue-600">Total Todos</p>
              <p className="text-2xl font-bold">{stats.total_todos}</p>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <p className="text-sm text-green-600">Completed</p>
              <p className="text-2xl font-bold">{stats.completed_todos}</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded">
              <p className="text-sm text-yellow-600">Completion Rate</p>
              <p className="text-2xl font-bold">{stats.completion_rate}%</p>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <p className="text-sm text-purple-600">Added Today</p>
              <p className="text-2xl font-bold">{stats.todos_created_today}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={addTodo} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="Add new todo"
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add
          </button>
        </div>
      </form>

      <div className="bg-white rounded-lg shadow-md">
        {todos.map(todo => (
          <div
            key={todo.id}
            className="flex items-center gap-4 p-4 border-b last:border-b-0"
          >
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo)}
              className="h-5 w-5 rounded border-gray-300 focus:ring-blue-500"
            />
            <span className={todo.completed ? 'line-through text-gray-500' : ''}>
              {todo.title}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;