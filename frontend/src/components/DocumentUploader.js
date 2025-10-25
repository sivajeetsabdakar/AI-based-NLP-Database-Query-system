/**
 * Document Uploader Component
 * Drag-and-drop document upload with progress tracking
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import apiService from '../services/api';
import './DocumentUploader.css';

const DocumentUploader = ({ onUploadSuccess, onUploadError }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadResults, setUploadResults] = useState(null);
  const [error, setError] = useState(null);
  const [docType, setDocType] = useState('');
  const [userSessionId, setUserSessionId] = useState('');

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    setError(null);
    
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const rejectionErrors = rejectedFiles.map(file => 
        `${file.file.name}: ${file.errors.map(e => e.message).join(', ')}`
      );
      setError(`File validation errors: ${rejectionErrors.join('; ')}`);
    }

    // Handle accepted files
    if (acceptedFiles.length > 0) {
      const newFiles = acceptedFiles.map(file => ({
        file,
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'pending',
        progress: 0
      }));
      
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  });

  const removeFile = (fileId) => {
    setFiles(prevFiles => prevFiles.filter(f => f.id !== fileId));
  };

  const clearAllFiles = () => {
    setFiles([]);
    setUploadResults(null);
    setError(null);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType) => {
    if (fileType.includes('pdf')) return '📄';
    if (fileType.includes('word') || fileType.includes('document')) return '📝';
    if (fileType.includes('text')) return '📃';
    if (fileType.includes('csv')) return '📊';
    return '📁';
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResults(null);

    try {
      const fileObjects = files.map(f => f.file);
      const response = await apiService.uploadDocuments(fileObjects, userSessionId, docType);
      
      if (response.success) {
        setUploadResults(response);
        
        // Update file statuses
        setFiles(prevFiles => 
          prevFiles.map(f => ({ ...f, status: 'completed', progress: 100 }))
        );
        
        if (onUploadSuccess) {
          onUploadSuccess(response);
        }
      } else {
        throw new Error(response.error || 'Upload failed');
      }
    } catch (error) {
      setError(error.message || 'Upload failed');
      
      // Update file statuses
      setFiles(prevFiles => 
        prevFiles.map(f => ({ ...f, status: 'error', progress: 0 }))
      );
      
      if (onUploadError) {
        onUploadError(error);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleBatchUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadResults(null);

    try {
      const fileObjects = files.map(f => f.file);
      const response = await apiService.batchUploadDocuments(fileObjects, userSessionId);
      
      if (response.success) {
        setUploadResults(response);
        
        // Update file statuses
        setFiles(prevFiles => 
          prevFiles.map(f => ({ ...f, status: 'completed', progress: 100 }))
        );
        
        if (onUploadSuccess) {
          onUploadSuccess(response);
        }
      } else {
        throw new Error(response.error || 'Batch upload failed');
      }
    } catch (error) {
      setError(error.message || 'Batch upload failed');
      
      // Update file statuses
      setFiles(prevFiles => 
        prevFiles.map(f => ({ ...f, status: 'error', progress: 0 }))
      );
      
      if (onUploadError) {
        onUploadError(error);
      }
    } finally {
      setUploading(false);
    }
  };

  const renderFileList = () => {
    if (files.length === 0) return null;

    return (
      <div className="file-list">
        <div className="file-list-header">
          <h4>Selected Files ({files.length})</h4>
          <button 
            className="btn btn-outline-danger btn-sm"
            onClick={clearAllFiles}
            disabled={uploading}
          >
            Clear All
          </button>
        </div>
        
        <div className="files-grid">
          {files.map((file) => (
            <div key={file.id} className={`file-item ${file.status}`}>
              <div className="file-icon">
                {getFileIcon(file.type)}
              </div>
              
              <div className="file-info">
                <div className="file-name" title={file.name}>
                  {file.name}
                </div>
                <div className="file-details">
                  <span className="file-size">{formatFileSize(file.size)}</span>
                  <span className="file-type">{file.type}</span>
                </div>
              </div>
              
              <div className="file-status">
                {file.status === 'pending' && (
                  <span className="status-pending">Pending</span>
                )}
                {file.status === 'uploading' && (
                  <div className="status-uploading">
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${file.progress}%` }}
                      ></div>
                    </div>
                    <span>{file.progress}%</span>
                  </div>
                )}
                {file.status === 'completed' && (
                  <span className="status-completed">✓</span>
                )}
                {file.status === 'error' && (
                  <span className="status-error">✗</span>
                )}
              </div>
              
              <button
                className="btn-remove"
                onClick={() => removeFile(file.id)}
                disabled={uploading}
                title="Remove file"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderUploadResults = () => {
    if (!uploadResults) return null;

    return (
      <div className="upload-results">
        <div className="results-header">
          <h4>Upload Results</h4>
          <span className={`results-status ${uploadResults.success ? 'success' : 'error'}`}>
            {uploadResults.success ? 'Success' : 'Failed'}
          </span>
        </div>
        
        <div className="results-content">
          {uploadResults.success && (
            <div className="success-details">
              <div className="result-item">
                <span className="label">Document ID:</span>
                <span className="value">{uploadResults.document_id}</span>
              </div>
              <div className="result-item">
                <span className="label">Document Type:</span>
                <span className="value">{uploadResults.doc_type}</span>
              </div>
              <div className="result-item">
                <span className="label">Chunks Created:</span>
                <span className="value">{uploadResults.chunks_count}</span>
              </div>
              <div className="result-item">
                <span className="label">Processing Time:</span>
                <span className="value">{uploadResults.processing_time?.toFixed(2)}s</span>
              </div>
            </div>
          )}
          
          {uploadResults.total_documents && (
            <div className="batch-details">
              <div className="result-item">
                <span className="label">Total Documents:</span>
                <span className="value">{uploadResults.total_documents}</span>
              </div>
              <div className="result-item">
                <span className="label">Processed:</span>
                <span className="value success">{uploadResults.processed_documents}</span>
              </div>
              <div className="result-item">
                <span className="label">Failed:</span>
                <span className="value error">{uploadResults.failed_documents}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="document-uploader">
      <div className="uploader-header">
        <h2>Document Upload</h2>
        <p>Upload documents for processing and indexing</p>
      </div>

      <div className="upload-options">
        <div className="form-group">
          <label htmlFor="docType">Document Type (Optional)</label>
          <select
            id="docType"
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="form-control"
          >
            <option value="">Auto-detect</option>
            <option value="resume">Resume</option>
            <option value="contract">Contract</option>
            <option value="review">Performance Review</option>
            <option value="policy">Policy Document</option>
            <option value="general">General Document</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="userSessionId">User Session ID (Optional)</label>
          <input
            type="text"
            id="userSessionId"
            value={userSessionId}
            onChange={(e) => setUserSessionId(e.target.value)}
            placeholder="session_12345"
            className="form-control"
          />
        </div>
      </div>

      <div className="dropzone-container">
        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'active' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="dropzone-content">
            <div className="dropzone-icon">📁</div>
            <div className="dropzone-text">
              {isDragActive ? (
                <p>Drop the files here...</p>
              ) : (
                <div>
                  <p>Drag & drop files here, or click to select files</p>
                  <p className="dropzone-hint">
                    Supports PDF, DOCX, TXT, CSV files (max 50MB each)
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {renderFileList()}

      {files.length > 0 && (
        <div className="upload-actions">
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Files'}
          </button>
          
          <button
            className="btn btn-success"
            onClick={handleBatchUpload}
            disabled={uploading}
          >
            {uploading ? 'Processing...' : 'Batch Upload'}
          </button>
        </div>
      )}

      {error && (
        <div className="alert alert-danger">
          <strong>Error:</strong> {error}
        </div>
      )}

      {renderUploadResults()}
    </div>
  );
};

export default DocumentUploader;
