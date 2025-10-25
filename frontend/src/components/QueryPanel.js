/**
 * Query Panel Component
 * Interface for natural language queries with auto-suggestions and history
 */
import React, { useState, useEffect, useRef } from 'react';
import apiService from '../services/api';
import './QueryPanel.css';

const QueryPanel = ({ onQueryResult, onQueryError }) => {
  const [query, setQuery] = useState('');
  const [queryHistory, setQueryHistory] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [queryType, setQueryType] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [processingTime, setProcessingTime] = useState(0);
  
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Load query history on component mount
  useEffect(() => {
    loadQueryHistory();
  }, []);

  // Load suggestions when query changes
  useEffect(() => {
    if (query.length > 2) {
      loadSuggestions();
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [query]);

  // Handle clicks outside suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadQueryHistory = async () => {
    try {
      const response = await apiService.getQueryHistory(20, 0);
      if (response.success) {
        setQueryHistory(response.queries || []);
      }
    } catch (error) {
      console.error('Failed to load query history:', error);
    }
  };

  const loadSuggestions = async () => {
    try {
      // This would typically call a suggestions API
      // For now, we'll use static suggestions based on common patterns
      const commonQueries = [
        'How many employees do we have?',
        'Show me all employees in Engineering',
        'What is the average salary by department?',
        'Find resumes with Python skills',
        'Show me performance reviews from last year',
        'List all contracts expiring this month',
        'Who are the top performers?',
        'What departments have the most employees?',
        'Find employees hired in the last 6 months',
        'Show me all policy documents'
      ];

      const filteredSuggestions = commonQueries.filter(suggestion =>
        suggestion.toLowerCase().includes(query.toLowerCase())
      );

      setSuggestions(filteredSuggestions.slice(0, 5));
      setShowSuggestions(filteredSuggestions.length > 0);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    }
  };

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setShowSuggestions(false);
    setShowHistory(false);

    const startTime = Date.now();

    try {
      // First classify the query
      const classificationResponse = await apiService.classifyQuery(query);
      
      if (classificationResponse.success) {
        setQueryType(classificationResponse.query_type);
        setConfidence(classificationResponse.confidence);
      }

      // Process the query
      const response = await apiService.processQuery(query);
      
      if (response.success) {
        setProcessingTime((Date.now() - startTime) / 1000);
        
        // Save to history
        const newQuery = {
          query: query,
          query_type: response.query_type,
          timestamp: new Date().toISOString(),
          results_count: response.total_results,
          processing_time: (Date.now() - startTime) / 1000
        };
        
        setQueryHistory(prev => [newQuery, ...prev.slice(0, 19)]);
        saveQueryToHistory(newQuery);
        
        if (onQueryResult) {
          onQueryResult(response);
        }
      } else {
        throw new Error(response.error || 'Query processing failed');
      }
    } catch (error) {
      setError(error.message || 'Query processing failed');
      
      if (onQueryError) {
        onQueryError(error);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const saveQueryToHistory = (queryData) => {
    try {
      const history = JSON.parse(localStorage.getItem('queryHistory') || '[]');
      const newHistory = [queryData, ...history.slice(0, 49)]; // Keep last 50 queries
      localStorage.setItem('queryHistory', JSON.stringify(newHistory));
    } catch (error) {
      console.error('Failed to save query to history:', error);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const handleHistoryClick = (historyItem) => {
    setQuery(historyItem.query);
    setShowHistory(false);
    inputRef.current?.focus();
  };

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setError(null);
  };

  const handleInputFocus = () => {
    if (query.length > 2) {
      setShowSuggestions(true);
    }
    setShowHistory(true);
  };

  const clearQuery = () => {
    setQuery('');
    setError(null);
    setQueryType('');
    setConfidence(0);
    setProcessingTime(0);
    inputRef.current?.focus();
  };

  const renderSuggestions = () => {
    if (!showSuggestions || suggestions.length === 0) return null;

    return (
      <div className="suggestions-dropdown" ref={suggestionsRef}>
        <div className="suggestions-header">
          <span>Suggestions</span>
        </div>
        {suggestions.map((suggestion, index) => (
          <div
            key={index}
            className="suggestion-item"
            onClick={() => handleSuggestionClick(suggestion)}
          >
            {suggestion}
          </div>
        ))}
      </div>
    );
  };

  const renderQueryHistory = () => {
    if (!showHistory || queryHistory.length === 0) return null;

    return (
      <div className="history-dropdown">
        <div className="history-header">
          <span>Recent Queries</span>
          <button
            className="btn-clear-history"
            onClick={() => {
              setQueryHistory([]);
              localStorage.removeItem('queryHistory');
            }}
          >
            Clear
          </button>
        </div>
        {queryHistory.slice(0, 10).map((historyItem, index) => (
          <div
            key={index}
            className="history-item"
            onClick={() => handleHistoryClick(historyItem)}
          >
            <div className="history-query">{historyItem.query}</div>
            <div className="history-meta">
              <span className="history-type">{historyItem.query_type}</span>
              <span className="history-time">
                {new Date(historyItem.timestamp).toLocaleDateString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderQueryInfo = () => {
    if (!queryType && !confidence && !processingTime) return null;

    return (
      <div className="query-info">
        {queryType && (
          <div className="info-item">
            <span className="label">Type:</span>
            <span className={`value type-${queryType.toLowerCase()}`}>
              {queryType.replace('_', ' ')}
            </span>
          </div>
        )}
        {confidence > 0 && (
          <div className="info-item">
            <span className="label">Confidence:</span>
            <span className="value">
              {(confidence * 100).toFixed(1)}%
            </span>
          </div>
        )}
        {processingTime > 0 && (
          <div className="info-item">
            <span className="label">Time:</span>
            <span className="value">
              {processingTime.toFixed(2)}s
            </span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="query-panel">
      <div className="panel-header">
        <h2>Natural Language Query</h2>
        <p>Ask questions about your data in plain English</p>
      </div>

      <form onSubmit={handleQuerySubmit} className="query-form">
        <div className="query-input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              value={query}
              onChange={handleInputChange}
              onFocus={handleInputFocus}
              placeholder="Ask a question about your data... (e.g., 'How many employees do we have?', 'Show me resumes with Python skills')"
              className="query-input"
              rows="3"
              disabled={isProcessing}
            />
            
            {query && (
              <button
                type="button"
                className="btn-clear"
                onClick={clearQuery}
                disabled={isProcessing}
                title="Clear query"
              >
                ×
              </button>
            )}
          </div>

          {renderSuggestions()}
          {renderQueryHistory()}
        </div>

        <div className="query-actions">
          <button
            type="submit"
            className="btn btn-primary btn-query"
            disabled={isProcessing || !query.trim()}
          >
            {isProcessing ? (
              <>
                <span className="spinner"></span>
                Processing...
              </>
            ) : (
              <>
                🔍 Ask Question
              </>
            )}
          </button>
        </div>

        {renderQueryInfo()}

        {error && (
          <div className="alert alert-danger">
            <strong>Error:</strong> {error}
          </div>
        )}
      </form>

      <div className="query-examples">
        <h4>Example Queries</h4>
        <div className="examples-grid">
          <div className="example-category">
            <h5>Employee Data</h5>
            <ul>
              <li>"How many employees do we have?"</li>
              <li>"Show me all employees in Engineering"</li>
              <li>"What is the average salary by department?"</li>
            </ul>
          </div>
          <div className="example-category">
            <h5>Document Search</h5>
            <ul>
              <li>"Find resumes with Python skills"</li>
              <li>"Show me performance reviews from last year"</li>
              <li>"List all contracts expiring this month"</li>
            </ul>
          </div>
          <div className="example-category">
            <h5>Analytics</h5>
            <ul>
              <li>"Who are the top performers?"</li>
              <li>"What departments have the most employees?"</li>
              <li>"Find employees hired in the last 6 months"</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QueryPanel;
