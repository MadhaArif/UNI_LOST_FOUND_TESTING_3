import React, { useEffect } from 'react';
import './App.css';

function App() {
  useEffect(() => {
    // Redirect to the backend-served HTML application
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
    window.location.href = backendUrl;
  }, []);

  return (
    <div className="App">
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '18px',
        color: '#48A6A7'
      }}>
        <div>
          <div>Redirecting to UMT Belongings Hub...</div>
          <div style={{ marginTop: '20px', fontSize: '14px' }}>
            If you are not redirected automatically, 
            <a href={process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001'} style={{ color: '#48A6A7', marginLeft: '5px' }}>
              click here
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;