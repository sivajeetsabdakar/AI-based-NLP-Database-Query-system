/**
 * Database Connector Component
 * Interface for database connection and schema discovery
 */
import React, { useState, useEffect } from 'react';
import apiService from '../services/api';
import './DatabaseConnector.css';

const DatabaseConnector = ({ onConnectionSuccess, onSchemaUpdate }) => {
  const [connectionString, setConnectionString] = useState('');
  const [connectionName, setConnectionName] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);
  const [schemaData, setSchemaData] = useState(null);
  const [error, setError] = useState(null);
  const [connectionHistory, setConnectionHistory] = useState([]);
  const [showSchema, setShowSchema] = useState(false);

  // Load connection history on component mount
  useEffect(() => {
    loadConnectionHistory();
  }, []);

  const loadConnectionHistory = () => {
    const history = localStorage.getItem('connectionHistory');
    if (history) {
      try {
        setConnectionHistory(JSON.parse(history));
      } catch (error) {
        console.error('Failed to load connection history:', error);
      }
    }
  };

  const saveConnectionHistory = (connection) => {
    const history = [...connectionHistory];
    const existingIndex = history.findIndex(conn => conn.url === connection.url);
    
    if (existingIndex >= 0) {
      history[existingIndex] = connection;
    } else {
      history.unshift(connection);
    }
    
    // Keep only last 10 connections
    const limitedHistory = history.slice(0, 10);
    setConnectionHistory(limitedHistory);
    localStorage.setItem('connectionHistory', JSON.stringify(limitedHistory));
  };

  const handleConnectionTest = async () => {
    if (!connectionString.trim()) {
      setError('Please enter a database connection string');
      return;
    }

    setIsConnecting(true);
    setError(null);
    setConnectionStatus(null);

    try {
      const response = await apiService.testDatabaseConnection(connectionString);
      
      if (response.success) {
        setConnectionStatus('connected');
        setError(null);
        
        // Save to history
        const connection = {
          url: connectionString,
          name: connectionName || 'Unnamed Connection',
          timestamp: new Date().toISOString()
        };
        saveConnectionHistory(connection);
        
        // Notify parent component
        if (onConnectionSuccess) {
          onConnectionSuccess(response);
        }
      } else {
        setConnectionStatus('failed');
        setError(response.error || 'Connection test failed');
      }
    } catch (error) {
      setConnectionStatus('failed');
      setError(error.message || 'Connection test failed');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSchemaDiscovery = async () => {
    if (!connectionString.trim()) {
      setError('Please enter a database connection string');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      const response = await apiService.connectDatabase({
        database_url: connectionString,
        connection_name: connectionName,
        test_connection: true
      });
      
      if (response.success) {
        setConnectionStatus('connected');
        setSchemaData(response.schema_info);
        setShowSchema(true);
        
        // Notify parent component
        if (onSchemaUpdate) {
          onSchemaUpdate(response.schema_info);
        }
      } else {
        setError(response.error || 'Schema discovery failed');
      }
    } catch (error) {
      setError(error.message || 'Schema discovery failed');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleHistorySelect = (connection) => {
    setConnectionString(connection.url);
    setConnectionName(connection.name);
  };

  const handleClearHistory = () => {
    setConnectionHistory([]);
    localStorage.removeItem('connectionHistory');
  };

  const renderConnectionStatus = () => {
    if (!connectionStatus) return null;

    const statusClasses = {
      connected: 'status-success',
      failed: 'status-error',
      testing: 'status-warning'
    };

    const statusMessages = {
      connected: 'Connection successful',
      failed: 'Connection failed',
      testing: 'Testing connection...'
    };

    return (
      <div className={`connection-status ${statusClasses[connectionStatus]}`}>
        <span className="status-indicator"></span>
        {statusMessages[connectionStatus]}
      </div>
    );
  };

  const renderSchemaVisualization = () => {
    if (!schemaData || !showSchema) return null;

    return (
      <div className="schema-visualization">
        <div className="schema-header">
          <h3>Discovered Schema</h3>
          <button 
            className="btn btn-sm btn-outline-secondary"
            onClick={() => setShowSchema(false)}
          >
            Hide Schema
          </button>
        </div>
        
        <div className="schema-content">
          <div className="schema-summary">
            <div className="summary-item">
              <span className="label">Tables:</span>
              <span className="value">{schemaData.tables_count || 0}</span>
            </div>
            <div className="summary-item">
              <span className="label">Relationships:</span>
              <span className="value">{schemaData.relationships_count || 0}</span>
            </div>
          </div>

          {schemaData.tables && (
            <div className="tables-list">
              <h4>Tables</h4>
              <div className="tables-grid">
                {Object.entries(schemaData.tables).map(([tableName, tableInfo]) => (
                  <div key={tableName} className="table-card">
                    <div className="table-header">
                      <h5>{tableName}</h5>
                      <span className="column-count">
                        {tableInfo.columns?.length || 0} columns
                      </span>
                    </div>
                    <div className="table-description">
                      {tableInfo.description || 'No description available'}
                    </div>
                    {tableInfo.columns && (
                      <div className="columns-list">
                        {tableInfo.columns.slice(0, 5).map((column, index) => (
                          <div key={index} className="column-item">
                            <span className="column-name">{column.name}</span>
                            <span className="column-type">{column.type}</span>
                          </div>
                        ))}
                        {tableInfo.columns.length > 5 && (
                          <div className="more-columns">
                            +{tableInfo.columns.length - 5} more columns
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {schemaData.relationships && (
            <div className="relationships-list">
              <h4>Relationships</h4>
              <div className="relationships-grid">
                {schemaData.relationships.map((relationship, index) => (
                  <div key={index} className="relationship-card">
                    <div className="relationship-info">
                      <span className="from-table">{relationship.from_table}</span>
                      <span className="relationship-type">{relationship.type}</span>
                      <span className="to-table">{relationship.to_table}</span>
                    </div>
                    <div className="relationship-details">
                      {relationship.from_column} → {relationship.to_column}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="database-connector">
      <div className="connector-header">
        <h2>Database Connection</h2>
        <p>Connect to your database and discover the schema</p>
      </div>

      <div className="connection-form">
        <div className="form-group">
          <label htmlFor="connectionName">Connection Name (Optional)</label>
          <input
            type="text"
            id="connectionName"
            value={connectionName}
            onChange={(e) => setConnectionName(e.target.value)}
            placeholder="My Database Connection"
            className="form-control"
          />
        </div>

        <div className="form-group">
          <label htmlFor="connectionString">Database Connection String</label>
          <textarea
            id="connectionString"
            value={connectionString}
            onChange={(e) => setConnectionString(e.target.value)}
            placeholder="postgresql://username:password@localhost:5432/database_name"
            className="form-control"
            rows="3"
          />
          <small className="form-text text-muted">
            Enter your database connection string (PostgreSQL, MySQL, SQLite, etc.)
          </small>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={handleConnectionTest}
            disabled={isConnecting || !connectionString.trim()}
            className="btn btn-primary"
          >
            {isConnecting ? 'Testing...' : 'Test Connection'}
          </button>
          
          <button
            type="button"
            onClick={handleSchemaDiscovery}
            disabled={isConnecting || !connectionString.trim()}
            className="btn btn-success"
          >
            {isConnecting ? 'Discovering...' : 'Discover Schema'}
          </button>
        </div>

        {renderConnectionStatus()}

        {error && (
          <div className="alert alert-danger">
            <strong>Error:</strong> {error}
          </div>
        )}
      </div>

      {connectionHistory.length > 0 && (
        <div className="connection-history">
          <div className="history-header">
            <h4>Connection History</h4>
            <button 
              className="btn btn-sm btn-outline-danger"
              onClick={handleClearHistory}
            >
              Clear History
            </button>
          </div>
          <div className="history-list">
            {connectionHistory.map((connection, index) => (
              <div key={index} className="history-item">
                <div className="history-info">
                  <div className="connection-name">{connection.name}</div>
                  <div className="connection-url">{connection.url}</div>
                  <div className="connection-time">
                    {new Date(connection.timestamp).toLocaleString()}
                  </div>
                </div>
                <button
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => handleHistorySelect(connection)}
                >
                  Use
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {renderSchemaVisualization()}
    </div>
  );
};

export default DatabaseConnector;
