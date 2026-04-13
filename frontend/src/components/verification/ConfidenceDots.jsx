import React from 'react';
import './ConfidenceDots.css';

const DOC_MAP = {
  aadhar: { label: 'A', fullName: 'Aadhar Card' },
  marksheet_10: { label: 'S', fullName: '10th Marksheet (SSC)' },
  marksheet_12: { label: 'I', fullName: '12th Marksheet (Inter)' },
  rank_card: { label: 'R', fullName: 'Entrance Rank Card' }
};

const Dot = ({ doc }) => {
  const info = DOC_MAP[doc.type] || { label: '?', fullName: doc.type };
  const levelClass = doc.badge; // high, medium, low
  const score = Math.round(doc.confidence * 100);
  
  // Icon choice based on requirements: high (●), medium (◐), low (○)
  const getIcon = () => {
    if (doc.badge === 'high') return '●';
    if (doc.badge === 'medium') return '◐';
    return '○';
  };

  const tooltip = `${info.fullName} — ${score / 100} (${doc.badge.toUpperCase()})`;

  return (
    <div className="conf-dot-item" title={tooltip} aria-label={tooltip}>
      <span className={`conf-dot-icon ${levelClass}`}>{getIcon()}</span>
      <span className="conf-dot-label">{info.label}</span>
    </div>
  );
};

export const ConfidenceDots = ({ documents }) => {
  // Ensure we have all 4 types represented even if missing
  const allDocTypes = ['aadhar', 'marksheet_10', 'marksheet_12', 'rank_card'];
  
  return (
    <div className="confidence-dots-container">
      {allDocTypes.map(type => {
        const doc = documents?.find(d => d.type === type) || { 
          type, 
          confidence: 0, 
          badge: 'none' 
        };
        return <Dot key={type} doc={doc} />;
      })}
    </div>
  );
};
