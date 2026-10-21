import React from 'react';
import { Award, AlertCircle } from 'lucide-react';

export default function MarksSummary({ obtainedMarks, totalMarks = 10.0 }) {
  if (obtainedMarks === null || obtainedMarks === undefined) {
    return (
      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', color: '#64748b', fontSize: '0.85rem' }}>
        <AlertCircle size={15} color="#94a3b8" />
        <span>Assessment marks not yet available.</span>
      </div>
    );
  }

  const ratio = totalMarks > 0 ? (obtainedMarks / totalMarks) : 0;
  const percentage = Math.round(ratio * 100);

  let badgeColor = '#10b981'; // Green
  let badgeBg = '#ecfdf5';
  let badgeBorder = '#a7f3d0';

  if (ratio < 0.5) {
    badgeColor = '#ef4444'; // Red
    badgeBg = '#fef2f2';
    badgeBorder = '#fecaca';
  } else if (ratio < 0.75) {
    badgeColor = '#f59e0b'; // Amber
    badgeBg = '#fffbeb';
    badgeBorder = '#fde68a';
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 12px',
          borderRadius: '8px',
          backgroundColor: badgeBg,
          color: badgeColor,
          border: `1px solid ${badgeBorder}`,
          fontWeight: 700,
          fontSize: '0.9rem',
        }}
      >
        <Award size={16} />
        <span>
          {obtainedMarks} / {totalMarks} Marks ({percentage}%)
        </span>
      </div>

      <div style={{ width: '120px', backgroundColor: '#e2e8f0', borderRadius: '10px', height: '8px', overflow: 'hidden' }}>
        <div
          style={{
            width: `${Math.min(100, Math.max(0, percentage))}%`,
            height: '100%',
            backgroundColor: badgeColor,
            borderRadius: '10px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
}
