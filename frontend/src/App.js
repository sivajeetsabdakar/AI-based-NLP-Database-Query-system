import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// Import components
import DatabaseConnector from './components/DatabaseConnector';
import DocumentUploader from './components/DocumentUploader';
import QueryPanel from './components/QueryPanel';
import ResultsView from './components/ResultsView';

function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [databaseConnected, setDatabaseConnected] = useState(false);
  const [schemaData, setSchemaData] = useState(null);
  const [queryResults, setQueryResults] = useState(null);
  const [processingTime, setProcessingTime] = useState(0);

  const handleDatabaseConnection = (connectionData) => {
    setDatabaseConnected(true);
    setCurrentStep(2);
  };

  const handleSchemaUpdate = (schema) => {
    setSchemaData(schema);
  };

  const handleDocumentUpload = (uploadData) => {
    setCurrentStep(3);
  };

  const handleQueryResult = (results) => {
    setQueryResults(results);
    setCurrentStep(4);
  };

  const handleQueryError = (error) => {
    console.error('Query error:', error);
  };

  const resetApplication = () => {
    setCurrentStep(1);
    setDatabaseConnected(false);
    setSchemaData(null);
    setQueryResults(null);
    setProcessingTime(0);
  };

  return (
    <Router>
      <div className="App">
        <header className="App-header">
          <h1>NLP Query Engine for Employee Data</h1>
          <p>Natural language query system for employee databases with dynamic schema discovery</p>
        </header>
        
        <main className="container-fluid">
          <div className="row">
            <div className="col-12">
              {/* Progress Indicator */}
              <div className="progress-indicator">
                <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
                  <div className="step-number">1</div>
                  <div className="step-label">Connect Database</div>
                </div>
                <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
                  <div className="step-number">2</div>
                  <div className="step-label">Upload Documents</div>
                </div>
                <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
                  <div className="step-number">3</div>
                  <div className="step-label">Query Data</div>
                </div>
                <div className={`step ${currentStep >= 4 ? 'active' : ''}`}>
                  <div className="step-number">4</div>
                  <div className="step-label">View Results</div>
                </div>
              </div>

              {/* Main Content */}
              <div className="main-content">
                {currentStep === 1 && (
                  <DatabaseConnector
                    onConnectionSuccess={handleDatabaseConnection}
                    onSchemaUpdate={handleSchemaUpdate}
                  />
                )}

                {currentStep === 2 && (
                  <DocumentUploader
                    onUploadSuccess={handleDocumentUpload}
                    onUploadError={(error) => console.error('Upload error:', error)}
                  />
                )}

                {currentStep === 3 && (
                  <QueryPanel
                    onQueryResult={handleQueryResult}
                    onQueryError={handleQueryError}
                  />
                )}

                {currentStep === 4 && queryResults && (
                  <ResultsView
                    results={queryResults}
                    queryType={queryResults.query_type}
                    processingTime={queryResults.processing_time}
                    onExport={(data, format) => {
                      console.log('Export data:', data, 'Format:', format);
                    }}
                  />
                )}
              </div>

              {/* Navigation */}
              <div className="navigation">
                <button
                  className="btn btn-outline-secondary"
                  onClick={resetApplication}
                >
                  Start Over
                </button>
                
                {currentStep > 1 && (
                  <button
                    className="btn btn-outline-primary"
                    onClick={() => setCurrentStep(currentStep - 1)}
                  >
                    Previous Step
                  </button>
                )}
                
                {currentStep < 4 && databaseConnected && (
                  <button
                    className="btn btn-primary"
                    onClick={() => setCurrentStep(currentStep + 1)}
                  >
                    Next Step
                  </button>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
