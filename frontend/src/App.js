import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      {/* This is a placeholder React app that serves the existing HTML files via iframe */}
      <iframe 
        src="/static-html/" 
        style={{
          width: '100%',
          height: '100vh',
          border: 'none',
          margin: 0,
          padding: 0
        }}
        title="UMT Belongings Hub"
      />
    </div>
  );
}

export default App;