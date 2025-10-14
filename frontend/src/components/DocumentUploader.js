// frontend/src/components/DocumentUploader.js

import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

export default function DocumentUploader() {
  const [isUploading, setIsUploading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [files, setFiles] = useState([]);

  const onDrop = acceptedFiles => {
    // Only accept files that are not empty and store them
    setFiles(acceptedFiles.filter(f => f.size > 0));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  const handleUpload = async () => {
    if (files.length === 0) {
      setStatusMsg('Please select files first.');
      return;
    }

    setIsUploading(true);
    setStatusMsg(`Uploading ${files.length} file(s)...`);

    const formData = new FormData();
    files.forEach(file => {
      // 'files' key must match the name expected by FastAPI's UploadFile list
      formData.append('files', file); 
    });

    try {
      const res = await axios.post('/api/upload-documents', formData, {
        headers: {
          // Necessary to correctly send multipart form data
          'Content-Type': 'multipart/form-data', 
        },
      });
      setStatusMsg(`Ingestion successful. Processed ${res.data.processed_chunks} chunks.`);
      setFiles([]); // Clear files after successful upload
    } catch (e) {
      setStatusMsg(`Upload Error: ${e.response?.data?.detail || e.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="card" style={{ padding: '20px', border: '1px solid #ddd' }}>
      <h3>Document Uploader 📄</h3>
      <div {...getRootProps()} 
           style={{ 
               border: `2px dashed ${isDragActive ? '#007bff' : '#aaa'}`, 
               padding: '20px', 
               textAlign: 'center', 
               cursor: 'pointer',
               backgroundColor: isDragActive ? '#f0f8ff' : '#fff'
           }}
      >
        <input {...getInputProps()} />
        {isDragActive 
          ? <p>Drop the files here...</p> 
          : <p>Drag 'n' drop documents (PDF, TXT, etc.) here, or click to select files.</p>
        }
      </div>
      
      {files.length > 0 && (
        <aside style={{ marginTop: '10px' }}>
          <h4>Files ready: {files.length}</h4>
        </aside>
      )}

      <button 
        onClick={handleUpload} 
        disabled={isUploading || files.length === 0} 
        style={{ marginTop: '10px', padding: '10px', backgroundColor: '#4CAF50', color: 'white', border: 'none', cursor: isUploading || files.length === 0 ? 'not-allowed' : 'pointer' }}
      >
        {isUploading ? 'Processing...' : `Start Ingestion (${files.length} files)`}
      </button>
      <div style={{ marginTop: '10px', fontWeight: 'bold' }}>{statusMsg}</div>
    </div>
  );
}