import React, { useRef, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import Message from './Message';
import './ChatWindow.css';

const ChatWindow = ({ messages, onSendMessage, isLoading }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <>
      <div className="chat-window" role="log" aria-live="polite">
        {messages.map((msg, index) => (
          <Message key={index} message={msg} />
        ))}
        {isLoading && (
          <div className="message-container message-assistant">
            <div className="message-bubble loading-bubble">
              Typing...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-container">
        <form className="floating-input" onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask about CYP2D6 drug interactions..."
            disabled={isLoading}
            aria-label="Message input"
          />
          <button type="submit" disabled={isLoading || !inputValue.trim()}>
            Send
          </button>
        </form>
      </div>
    </>
  );
};

ChatWindow.propTypes = {
  messages: PropTypes.arrayOf(
    PropTypes.shape({
      role: PropTypes.string.isRequired,
      content: PropTypes.string.isRequired,
      citations: PropTypes.array,
      is_substrate: PropTypes.string
    })
  ).isRequired,
  onSendMessage: PropTypes.func.isRequired,
  isLoading: PropTypes.bool.isRequired
};

export default ChatWindow;
