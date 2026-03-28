import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="header">
        <h1>CYP2D6 Medical Assistant</h1>
      </header>
      
      <main className="chat-window">
        {/* Chat messages will go here */}
      </main>
      
      <div className="input-container">
        <form className="floating-input" onSubmit={(e) => e.preventDefault()}>
          <input type="text" placeholder="Ask about CYP2D6 drug interactions..." />
          <button type="submit">Send</button>
        </form>
      </div>
      
      <footer className="medical-disclaimer">
        Disclaimer: This tool is for informational purposes only and does not constitute medical advice.
      </footer>
    </div>
  );
}

export default App;