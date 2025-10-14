// frontend/src/components/DatabaseConnector.js

import React, { useState } from "react";
import axios from "axios";

export default function DatabaseConnector() {
  const [conn, setConn] = useState("");
  const [schema, setSchema] = useState(null);
  const [msg, setMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function testConnect() {
    setMsg("Connecting...");
    setSchema(null); 
    setIsLoading(true);

    // Connection string check: we are using 'postgresql+psycopg2' but the placeholder is 'postgresql'
    // Ensure the user inputs the correct format for the backend driver.
    const connectionStringToSend = conn.includes("+") ? conn : conn.replace("postgresql://", "postgresql+psycopg2://");

    try {
      // POST request to the backend endpoint
      const res = await axios.post("/api/connect-database", { connection_string: connectionStringToSend }); 
      setSchema(res.data.schema);
      setMsg("Connected successfully! Schema analyzed.");
    } catch (e) {
      // Improved error handling based on the common error
      const errorDetail = e.response?.data?.detail || e.message;
      if (errorDetail.includes("FATAL: password authentication failed")) {
          setMsg("Error: Connection Failed. Check Username/Password/Port (e.g., demo:demo@localhost:5432).");
      } else if (errorDetail.includes("could not translate host name")) {
          setMsg("Error: Host Not Found. Check if your Docker container is running or if the host name is correct.");
      } else {
          setMsg("Error: " + errorDetail);
      }
    } finally {
        setIsLoading(false);
    }
  }

  return (
    <div className="card" style={{ padding: '20px', border: '1px solid #ddd' }}>
      <h3>Database Connector 💾</h3>
      <input
        value={conn}
        onChange={e => setConn(e.target.value)}
        placeholder="e.g., postgresql+psycopg2://user:pass@localhost:5432/demo"
        style={{ width: '100%', padding: '8px', marginBottom: '10px', boxSizing: 'border-box' }}
        disabled={isLoading}
      />
      <button 
        onClick={testConnect} 
        disabled={!conn || isLoading}
        style={{ padding: '10px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', cursor: (!conn || isLoading) ? 'not-allowed' : 'pointer' }}
      >
        {isLoading ? 'Analyzing...' : 'Connect & Analyze'}
      </button>
      <div style={{ marginTop: '10px', fontWeight: 'bold' }}>{msg}</div>
      
      {/* Schema Display Logic */}
      {schema && schema.tables && (
        <div style={{ marginTop: '15px', padding: '10px', borderTop: '1px solid #eee' }}>
          <h4>Discovered Schema:</h4>
          {Object.entries(schema.tables).map(([tableName, tableInfo]) => (
            <div key={tableName} style={{ marginBottom: '10px', borderLeft: '3px solid #007bff', paddingLeft: '8px' }}>
              <strong style={{ display: 'block' }}>{tableName.toUpperCase()}</strong>
              <ul style={{ listStyleType: 'disc', margin: '5px 0 0 20px', padding: 0 }}>
                {tableInfo.columns.map(col => (
                  <li key={col.name} style={{ fontSize: '0.9em' }}>
                    {col.name} (<span style={{ color: '#555' }}>{col.type}</span>)
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}