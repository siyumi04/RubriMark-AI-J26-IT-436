import React from 'react';
import { ThumbsUp, ThumbsDown, MessageSquareText, Sparkles } from 'lucide-react';

export default function FeedbackPanel({ feedback }) {
  if (!feedback) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
        <MessageSquareText size={32} style={{ margin: '0 auto 8px auto', display: 'block', color: '#cbd5e1' }} />
        Select or analyze an answer to inspect personalized AI feedback.
      </div>
    );
  }

  const { strengths, weaknesses, personalized_feedback } = feedback;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          <Sparkles size={18} color="#4f46e5" />
          <span>Personalized Academic Feedback</span>
        </h3>
        <span className="badge badge-purple">Explainable Rubric Synthesis</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        {/* Strengths */}
        <div
          style={{
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '10px',
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#166534', fontWeight: 600, marginBottom: '8px' }}>
            <ThumbsUp size={16} />
            <span>Demonstrated Strengths</span>
          </div>
          <p style={{ fontSize: '0.88rem', color: '#14532d', lineHeight: 1.5 }}>
            {strengths || 'Consistent response framing according to rubric standards.'}
          </p>
        </div>

        {/* Weaknesses */}
        <div
          style={{
            backgroundColor: '#fff1f2',
            border: '1px solid #fecdd3',
            borderRadius: '10px',
            padding: '16px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#9f1239', fontWeight: 600, marginBottom: '8px' }}>
            <ThumbsDown size={16} />
            <span>Areas for Improvement</span>
          </div>
          <p style={{ fontSize: '0.88rem', color: '#881337', lineHeight: 1.5 }}>
            {weaknesses || 'Minor refinement in technical terminology and precision recommended.'}
          </p>
        </div>
      </div>

      {/* Narrative Personalized Feedback */}
      <div
        style={{
          background: 'linear-gradient(135deg, #f8fafc, #f1f5f9)',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          padding: '20px',
          borderLeft: '4px solid #4f46e5',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, color: '#312e81', marginBottom: '10px' }}>
          <MessageSquareText size={18} color="#4f46e5" />
          <span>Lecturer & Student Actionable Guidance</span>
        </div>
        <p style={{ fontSize: '0.92rem', color: '#1e293b', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {personalized_feedback}
        </p>
      </div>
    </div>
  );
}
