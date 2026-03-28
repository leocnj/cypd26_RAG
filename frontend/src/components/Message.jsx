import React from 'react';
import CitationCard from './CitationCard';
import './Message.css';

const Message = ({ message }) => {
  const { role, content, citations, is_substrate } = message;
  const isUser = role === 'user';

  return (
    <div className={`message-container message-${role}`}>
      <div className="message-bubble">
        {!isUser && is_substrate && (
          <div className="message-status">
            <span className={`badge badge-${is_substrate.toLowerCase()}`}>
              {is_substrate === 'Substrate' ? 'Substrate' : 
               is_substrate === 'Non-substrate' ? 'Non-substrate' : 
               is_substrate === 'Inhibitor' ? 'Inhibitor' : is_substrate}
            </span>
          </div>
        )}
        <div className="message-content">{content}</div>
        {!isUser && citations && citations.length > 0 && (
          <div className="citations-container">
            <small>Sources:</small>
            {citations.map((cit, idx) => (
              <CitationCard key={idx} citation={cit} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
