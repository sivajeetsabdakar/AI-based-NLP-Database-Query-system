/**
 * Results View Component
 * Display results for SQL, document, and hybrid queries
 */
import React, { useState, useEffect } from 'react';
import './ResultsView.css';

const ResultsView = ({ results, queryType, processingTime, onExport }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filterText, setFilterText] = useState('');
  const [viewMode, setViewMode] = useState('table'); // table, card, combined

  const totalResults = results?.total_results || 0;
  const resultItems = results?.results || [];

  // Reset pagination when results change
  useEffect(() => {
    setCurrentPage(1);
  }, [results]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleExport = (format) => {
    if (onExport) {
      onExport(resultItems, format);
    }
  };

  const renderSQLResults = () => {
    if (!resultItems.length) return null;

    const columns = Object.keys(resultItems[0] || {});
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = resultItems.slice(startIndex, endIndex);

    return (
      <div className="sql-results">
        <div className="results-header">
          <h3>SQL Query Results</h3>
          <div className="results-actions">
            <button
              className="btn btn-outline-primary btn-sm"
              onClick={() => handleExport('csv')}
            >
              Export CSV
            </button>
            <button
              className="btn btn-outline-primary btn-sm"
              onClick={() => handleExport('json')}
            >
              Export JSON
            </button>
          </div>
        </div>

        <div className="table-container">
          <table className="results-table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th
                    key={column}
                    onClick={() => handleSort(column)}
                    className={`sortable ${sortField === column ? `sort-${sortDirection}` : ''}`}
                  >
                    {column}
                    {sortField === column && (
                      <span className="sort-indicator">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginatedItems.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column}>
                      {row[column] !== null && row[column] !== undefined 
                        ? String(row[column]) 
                        : '-'
                      }
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {renderPagination()}
      </div>
    );
  };

  const renderDocumentResults = () => {
    if (!resultItems.length) return null;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = resultItems.slice(startIndex, endIndex);

    return (
      <div className="document-results">
        <div className="results-header">
          <h3>Document Search Results</h3>
          <div className="results-actions">
            <button
              className="btn btn-outline-primary btn-sm"
              onClick={() => handleExport('json')}
            >
              Export JSON
            </button>
          </div>
        </div>

        <div className="documents-grid">
          {paginatedItems.map((item, index) => (
            <div key={index} className="document-card">
              <div className="document-header">
                <div className="document-title">
                  {item.metadata?.filename || `Document ${index + 1}`}
                </div>
                <div className="document-score">
                  Similarity: {(item.similarity_score * 100).toFixed(1)}%
                </div>
              </div>
              
              <div className="document-content">
                <div className="document-text">
                  {item.document?.substring(0, 200)}
                  {item.document?.length > 200 && '...'}
                </div>
              </div>
              
              <div className="document-metadata">
                <div className="metadata-item">
                  <span className="label">Type:</span>
                  <span className="value">{item.metadata?.doc_type || 'Unknown'}</span>
                </div>
                <div className="metadata-item">
                  <span className="label">Collection:</span>
                  <span className="value">{item.collection || 'Unknown'}</span>
                </div>
                {item.metadata?.section_type && (
                  <div className="metadata-item">
                    <span className="label">Section:</span>
                    <span className="value">{item.metadata.section_type}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {renderPagination()}
      </div>
    );
  };

  const renderHybridResults = () => {
    if (!resultItems.length) return null;

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = resultItems.slice(startIndex, endIndex);

    return (
      <div className="hybrid-results">
        <div className="results-header">
          <h3>Hybrid Query Results</h3>
          <div className="results-actions">
            <button
              className="btn btn-outline-primary btn-sm"
              onClick={() => handleExport('json')}
            >
              Export JSON
            </button>
          </div>
        </div>

        <div className="hybrid-items">
          {paginatedItems.map((item, index) => (
            <div key={index} className={`hybrid-item ${item.type}`}>
              <div className="item-header">
                <div className="item-type">
                  {item.type === 'sql' ? '🗄️ Database' : '📄 Document'}
                </div>
                <div className="item-rank">#{item.rank}</div>
              </div>
              
              <div className="item-content">
                {item.type === 'sql' ? (
                  <div className="sql-item">
                    <div className="sql-data">
                      {Object.entries(item.data).map(([key, value]) => (
                        <div key={key} className="sql-field">
                          <span className="field-name">{key}:</span>
                          <span className="field-value">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="document-item">
                    <div className="document-text">
                      {item.data.document?.substring(0, 300)}
                      {item.data.document?.length > 300 && '...'}
                    </div>
                    <div className="document-meta">
                      <span>Score: {(item.data.similarity_score * 100).toFixed(1)}%</span>
                      <span>Source: {item.data.metadata?.filename || 'Unknown'}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {renderPagination()}
      </div>
    );
  };

  const renderPagination = () => {
    const totalPages = Math.ceil(totalResults / itemsPerPage);
    if (totalPages <= 1) return null;

    const pageNumbers = [];
    for (let i = 1; i <= totalPages; i++) {
      pageNumbers.push(i);
    }

    return (
      <div className="pagination">
        <div className="pagination-info">
          Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, totalResults)} of {totalResults} results
        </div>
        
        <div className="pagination-controls">
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          
          <div className="page-numbers">
            {pageNumbers.slice(Math.max(0, currentPage - 3), currentPage + 2).map(page => (
              <button
                key={page}
                className={`btn btn-sm ${page === currentPage ? 'btn-primary' : 'btn-outline-secondary'}`}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}
          </div>
          
          <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  const renderResultsSummary = () => {
    if (!results) return null;

    return (
      <div className="results-summary">
        <div className="summary-item">
          <span className="label">Query Type:</span>
          <span className={`value type-${queryType?.toLowerCase()}`}>
            {queryType?.replace('_', ' ')}
          </span>
        </div>
        <div className="summary-item">
          <span className="label">Total Results:</span>
          <span className="value">{totalResults}</span>
        </div>
        {processingTime && (
          <div className="summary-item">
            <span className="label">Processing Time:</span>
            <span className="value">{processingTime.toFixed(2)}s</span>
          </div>
        )}
        {results.confidence && (
          <div className="summary-item">
            <span className="label">Confidence:</span>
            <span className="value">{(results.confidence * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>
    );
  };

  if (!results || !resultItems.length) {
    return (
      <div className="results-view">
        <div className="no-results">
          <div className="no-results-icon">🔍</div>
          <h3>No Results Found</h3>
          <p>Try adjusting your query or search criteria</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-view">
      <div className="results-controls">
        <div className="controls-left">
          <div className="items-per-page">
            <label htmlFor="itemsPerPage">Items per page:</label>
            <select
              id="itemsPerPage"
              value={itemsPerPage}
              onChange={(e) => setItemsPerPage(Number(e.target.value))}
              className="form-control"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
        
        <div className="controls-right">
          <div className="view-mode">
            <button
              className={`btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setViewMode('table')}
            >
              Table
            </button>
            <button
              className={`btn btn-sm ${viewMode === 'card' ? 'btn-primary' : 'btn-outline-secondary'}`}
              onClick={() => setViewMode('card')}
            >
              Cards
            </button>
          </div>
        </div>
      </div>

      {renderResultsSummary()}

      {queryType === 'SQL_QUERY' && renderSQLResults()}
      {queryType === 'DOCUMENT_QUERY' && renderDocumentResults()}
      {queryType === 'HYBRID_QUERY' && renderHybridResults()}
    </div>
  );
};

export default ResultsView;
