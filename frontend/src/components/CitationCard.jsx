import React from 'react';
import PropTypes from 'prop-types';
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

  const innerContent = (
    <>
      <div className="citation-header">
        <span className="drug-id">{citation.drug_id || 'Unknown'}</span>
        {citation.name && <span className="drug-name"> - {citation.name}</span>}
      </div>
      {citation.smiles && (
        <div className="citation-body">
          <small className="smiles-text">SMILES: {citation.smiles}</small>
        </div>
      )}
    </>
  );

  return citation.drug_id ? (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="citation-card"
    >
      {innerContent}
    </a>
  ) : (
    <div className="citation-card">
      {innerContent}
    </div>
  );
};

CitationCard.propTypes = {
  citation: PropTypes.shape({
    drug_id: PropTypes.string,
    name: PropTypes.string,
    smiles: PropTypes.string
  })
};

export default CitationCard;
