import React from 'react';
import './CitationCard.css';

const CitationCard = ({ citation }) => {
  if (!citation) return null;

  let url = '#';
  if (citation.drug_id) {
    if (citation.drug_id.startsWith('DB')) {
      url = `https://go.drugbank.com/drugs/${citation.drug_id}`;
    } else {
      url = `https://pubchem.ncbi.nlm.nih.gov/compound/${citation.drug_id}`;
    }
  }

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="citation-card"
    >
      <div className="citation-header">
        <span className="drug-id">{citation.drug_id || 'Unknown'}</span>
        {citation.name && <span className="drug-name"> - {citation.name}</span>}
      </div>
      {citation.smiles && (
        <div className="citation-body">
          <small className="smiles-text">SMILES: {citation.smiles}</small>
        </div>
      )}
    </a>
  );
};

export default CitationCard;
