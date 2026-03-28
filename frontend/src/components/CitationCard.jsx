import React from 'react';
import './CitationCard.css';

const CitationCard = ({ citation }) => {
  if (!citation) return null;

  return (
    <div className="citation-card">
      <div className="citation-header">
        <span className="drug-id">{citation.drug_id || 'Unknown'}</span>
        {citation.name && <span className="drug-name"> - {citation.name}</span>}
      </div>
      {citation.smiles && (
        <div className="citation-body">
          <small className="smiles-text">SMILES: {citation.smiles}</small>
        </div>
      )}
    </div>
  );
};

export default CitationCard;
