import React from 'react';
import { AlertTriangle, CheckCircle, Cpu, Info } from 'lucide-react';

export default function MissingConceptsCard({ missingConcepts = [], aiStatus = 'model_inference' }) {
  const isModelUnavailable = aiStatus.includes('unavailable') || aiStatus.includes('error');

  const EXCLUDED_META = ['none clearly identified', 'requires human review'];
  const cleanedConcepts = missingConcepts.filter(
    (c) => c && !EXCLUDED_META.includes(c.trim().toLowerCase())
  );
  const requiresHumanReview = missingConcepts.some(
    (c) => c && c.trim().toLowerCase() === 'requires human review'
  );

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <AlertTriangle size={18} color={cleanedConcepts.length > 0 ? '#ef4444' : '#10b981'} />
          <span>Knowledge Gap Detection</span>
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {requiresHumanReview && (
            <span className="badge badge-amber" title="Requires instructor verification">
              Human Review Recommended
            </span>
          )}
          <span className={`badge ${cleanedConcepts.length > 0 ? 'badge-rose' : 'badge-emerald'}`}>
            {cleanedConcepts.length} Gaps Detected
          </span>
        </div>
      </div>

      {isModelUnavailable && (
        <div className="alert alert-warning" style={{ marginBottom: '14px' }}>
          <Cpu size={18} style={{ flexShrink: 0 }} />
          <div>
            <strong>AI Model Notice:</strong> {aiStatus}. Missing concepts detection requires the trained model to be placed in <code>backend/ml_models/feedback_model.joblib</code>.
          </div>
        </div>
      )}

      {cleanedConcepts.length === 0 ? (
        <div
          style={{
            padding: '24px',
            textAlign: 'center',
            backgroundColor: '#ecfdf5',
            borderRadius: '8px',
            border: '1px solid #a7f3d0',
            color: '#065f46',
          }}
        >
          <CheckCircle size={32} style={{ margin: '0 auto 8px auto', display: 'block', color: '#10b981' }} />
          <h4 style={{ fontWeight: 600, marginBottom: '4px' }}>No Knowledge Gaps Detected</h4>
          <p style={{ fontSize: '0.86rem', color: '#047857' }}>
            The student response covers all core conceptual requirements for this question prompt.
          </p>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: '14px' }}>
            The following essential concepts were identified as missing or insufficiently explained in the student's submission:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {cleanedConcepts.map((concept, idx) => (
              <span key={idx} className="concept-tag">
                <AlertTriangle size={12} />
                <span>{concept}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
