// frontend/src/components/QueryPanel.js

import React, { useState } from 'react';
import axios from 'axios';

export default function QueryPanel({ setResults }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // POST request to the backend query endpoint
      const res = await axios.post('/api/query', { query });
      setResults(res.data.results);
    } catch (e) {
      const errMsg = e.response?.data?.detail || e.message;
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Natural Language Query Interface 💬</h3>
      <form onSubmit={handleSubmit}>
        <input 
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g., How many employees do we have?"
          disabled={loading}
        />
        <button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Thinking...' : 'Query'}
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </div>
  );
}