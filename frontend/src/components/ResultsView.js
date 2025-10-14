// // frontend/src/components/ResultsView.js

// import React from 'react';

// // Renders the SQL table results
// const SQLTable = ({ data }) => {
//   if (!data || data.length === 0) return <p>No SQL results found.</p>;

//   const columns = Object.keys(data[0]);

//   return (
//     <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
//       <table style={{ borderCollapse: 'collapse', width: '100%', border: '1px solid #ddd' }}>
//         <thead>
//           <tr style={{ backgroundColor: '#f2f2f2' }}>
//             {columns.map(col => <th key={col} style={{ border: '1px solid #ddd', padding: '10px' }}>{col.toUpperCase()}</th>)}
//           </tr>
//         </thead>
//         <tbody>
//           {data.map((row, rowIndex) => (
//             <tr key={rowIndex}>
//               {columns.map(col => <td key={col} style={{ border: '1px solid #ddd', padding: '8px' }}>{row[col]}</td>)}
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   );
// };

// // Renders document snippets
// const DocCard = ({ doc, index }) => (
//   <div key={index} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px', borderRadius: '5px' }}>
//     <p style={{ fontWeight: 'bold', margin: '0 0 5px 0' }}>{index + 1}. Document Snippet (Score: {doc.score ? doc.score.toFixed(4) : 'N/A'})</p>
//     <p style={{ margin: 0, fontSize: '0.9em' }}>
//       "{doc.text.substring(0, 300)}{doc.text.length > 300 ? '...' : ''}"
//     </p>
//   </div>
// );

// export default function ResultsView({ results }) {
//   if (!results) return null;

//   const { query_type, sql_results, doc_results, sql_error, doc_error, generated_sql } = results;

//   return (
//     <div className="card" style={{ marginTop: '20px', padding: '20px', border: '1px solid #ddd' }}>
//       <h2>Query Results 🔍 ({query_type ? query_type.toUpperCase() : 'N/A'})</h2>
      
//       {/* SQL Results */}
//       {(query_type === 'sql' || query_type === 'hybrid') && (
//         <div style={{ marginTop: '15px' }}>
//           <h4>SQL Table Data</h4>
//           {generated_sql && <p style={{ fontSize: '0.8em', color: '#666' }}>SQL: <code>{generated_sql}</code></p>}
//           {sql_error ? (
//             <p style={{ color: 'red', fontWeight: 'bold' }}>SQL Error: {sql_error}</p>
//           ) : (
//             <SQLTable data={sql_results} />
//           )}
//         </div>
//       )}

//       {/* Document Results */}
//       {(query_type === 'doc' || query_type === 'hybrid') && (
//         <div style={{ marginTop: '15px' }}>
//           <h4>Document Snippets (RAG)</h4>
//           {doc_error ? (
//             <p style={{ color: 'red', fontWeight: 'bold' }}>Document Search Error: {doc_error}</p>
//           ) : doc_results && doc_results.length > 0 ? (
//             doc_results.map((doc, index) => <DocCard key={index} doc={doc} index={index} />)
//           ) : (
//             <p>No relevant document chunks found.</p>
//           )}
//         </div>
//       )}
//     </div>
//   );
// }
// frontend/src/components/ResultsView.js

import React from 'react';

// Renders the SQL table results
const SQLTable = ({ data }) => {
  if (!data || data.length === 0) return <p>No SQL results found.</p>;

  const columns = Object.keys(data[0]);

  return (
    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
      <table style={{ borderCollapse: 'collapse', width: '100%', border: '1px solid #ddd' }}>
        <thead>
          <tr style={{ backgroundColor: '#f2f2f2' }}>
            {columns.map(col => <th key={col} style={{ border: '1px solid #ddd', padding: '10px' }}>{col.toUpperCase()}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map(col => <td key={col} style={{ border: '1px solid #ddd', padding: '8px' }}>{row[col]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// Renders individual document snippet (used as fallback)
const DocCard = ({ doc, index }) => (
  <div key={index} style={{ border: '1px solid #ccc', padding: '10px', marginBottom: '10px', borderRadius: '5px' }}>
    <p style={{ fontWeight: 'bold', margin: '0 0 5px 0' }}>{index + 1}. Document Snippet (Score: {doc.score ? doc.score.toFixed(4) : 'N/A'})</p>
    <p style={{ margin: 0, fontSize: '0.9em' }}>
      "{doc.text.substring(0, 300)}{doc.text.length > 300 ? '...' : ''}"
    </p>
  </div>
);

export default function ResultsView({ results }) {
  if (!results) return null;

  const { query_type, sql_results, doc_results, doc_answer, sql_error, doc_error, generated_sql } = results;

  return (
    <div className="card" style={{ marginTop: '20px', padding: '20px', border: '1px solid #ddd' }}>
      <h2>Query Results 🔍 ({query_type ? query_type.toUpperCase() : 'N/A'})</h2>
      
      {/* SQL Results */}
      {(query_type === 'sql' || query_type === 'hybrid') && (
        <div style={{ marginTop: '15px' }}>
          <h4>SQL Table Data</h4>
          {generated_sql && <p style={{ fontSize: '0.8em', color: '#666' }}>SQL: <code>{generated_sql}</code></p>}
          {sql_error ? (
            <p style={{ color: 'red', fontWeight: 'bold' }}>SQL Error: {sql_error}</p>
          ) : (
            <SQLTable data={sql_results} />
          )}
        </div>
      )}

      {/* Document Results */}
      {(query_type === 'doc' || query_type === 'hybrid') && (
        <div style={{ marginTop: '15px' }}>
          <h4>Document Answer</h4>
          {doc_error ? (
            <p style={{ color: 'red', fontWeight: 'bold' }}>Document Search Error: {doc_error}</p>
          ) : doc_answer ? (
            <div style={{
              border: '1px solid #ccc',
              padding: '10px',
              borderRadius: '5px',
              backgroundColor: '#f9f9f9',
              fontSize: '0.95em'
            }}>
              {doc_answer}
            </div>
          ) : doc_results && doc_results.length > 0 ? (
            doc_results.map((doc, index) => <DocCard key={index} doc={doc} index={index} />)
          ) : (
            <p>No relevant document chunks found.</p>
          )}
        </div>
      )}
    </div>
  );
}
