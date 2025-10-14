// frontend/src/App.js

import React, { useState } from 'react';
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';
import './App.css'; // Use default create-react-app CSS or add basic styling

function App() {
  const [queryResults, setQueryResults] = useState(null);

  return (
    <div className="App" style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Hybrid NL-to-SQL Engine 🧠</h1>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '20px' }}>
          <div style={{ flex: 1 }}><DatabaseConnector /></div>
          <div style={{ flex: 1 }}><DocumentUploader /></div>
      </div>

      <QueryPanel setResults={setQueryResults} />
      
      <ResultsView results={queryResults} />
      
    </div>
  );
}

export default App;