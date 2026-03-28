import React from 'react';
import PropTypes from 'prop-types';
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
              {is_substrate}
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

Message.propTypes = {
  message: PropTypes.shape({
    role: PropTypes.string.isRequired,
    content: PropTypes.string.isRequired,
    citations: PropTypes.arrayOf(
      PropTypes.shape({
        drug_id: PropTypes.string,
        name: PropTypes.string,
        smiles: PropTypes.string
      })
    ),
    is_substrate: PropTypes.string
  }).isRequired
};

export default Message;
