import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import MissingConceptsCard from '../components/MissingConceptsCard';
import { BrainCircuit, AlertTriangle, CheckCircle, Lightbulb, GitMerge } from 'lucide-react';

export default function KnowledgeGapDetection({ activeStudent }) {
  const navigate = useNavigate();
  const [answers, setAnswers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modelStatus, setModelStatus] = useState(null);

  useEffect(() => {
    if (activeStudent) {
      loadData();
    }
  }, [activeStudent]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ansData, mStatus] = await Promise.all([
        apiService.getStudentAnswers(activeStudent.student_id),
        apiService.getModelStatus(),
      ]);
      setAnswers(ansData);
      setModelStatus(mStatus);
    } catch (err) {
      console.error('Failed to load gap data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!activeStudent) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
        <BrainCircuit size={36} color="#6366f1" style={{ margin: '0 auto 12px auto' }} />
        <h3>No Student Selected</h3>
        <p style={{ color: '#64748b' }}>Please select a student to analyze their knowledge gap profile.</p>
      </div>
    );
  }

  // Aggregate missing concepts across all submissions, excluding metadata labels
  const EXCLUDED_META = ['none clearly identified', 'requires human review'];
  const conceptCounts = {};
  let totalReviewFlags = 0;

  answers.forEach((ans) => {
    if (ans.feedback && ans.feedback.missing_concepts) {
      ans.feedback.missing_concepts.forEach((concept) => {
        if (!concept) return;
        const cLower = concept.trim().toLowerCase();
        if (cLower === 'requires human review') {
          totalReviewFlags += 1;
        }
        if (!EXCLUDED_META.includes(cLower)) {
          const cName = concept.trim();
          conceptCounts[cName] = (conceptCounts[cName] || 0) + 1;
        }
      });
    }
  });

  const uniqueConcepts = Object.keys(conceptCounts);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Knowledge Gap Detection Engine</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Conceptual deficiency profiling for <strong>{activeStudent.student_name}</strong> ({activeStudent.student_id})
          </p>
        </div>
        <button
          className="btn btn-primary"
          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          onClick={() => navigate('/concept-dependencies')}
        >
          <GitMerge size={16} />
          <span>Concept Dependency Analysis</span>
        </button>
      </div>

      {/* Model Transparency Banner */}
      <div className={`alert ${modelStatus?.model_loaded ? 'alert-success' : 'alert-warning'}`}>
        <BrainCircuit size={20} style={{ flexShrink: 0 }} />
        <div>
          <strong>Trained Model Engine Status:</strong> {modelStatus?.status_message || 'Initializing...'}
          {!modelStatus?.model_loaded && (
            <div style={{ marginTop: '4px', fontSize: '0.82rem' }}>
              Inference is operating in transparent fallback mode. To enable automatic missing concept extraction, place your trained Google Colab model artifact at <code>backend/ml_models/feedback_model.joblib</code>.
            </div>
          )}
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Unique Gaps Identified</h3>
            <span className="badge badge-rose">{uniqueConcepts.length} Concepts</span>
          </div>
          {uniqueConcepts.length === 0 ? (
            <div style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle size={18} />
              <span>No persistent conceptual gaps detected across assessed questions!</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {uniqueConcepts.map((concept) => (
                <span key={concept} className="concept-tag">
                  <AlertTriangle size={12} />
                  <span>{concept}</span>
                  <span style={{ opacity: 0.7, marginLeft: '4px' }}>({conceptCounts[concept]}x)</span>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Intervention Priority</h3>
            <span className="badge badge-indigo">Rubric Guidance</span>
          </div>
          <p style={{ fontSize: '0.9rem', color: '#64748b', lineHeight: 1.6 }}>
            {uniqueConcepts.length > 0
              ? `Targeted conceptual reinforcement is required for ${uniqueConcepts.slice(0, 3).join(', ')}. Addressing these areas directly elevates rubric alignment.`
              : 'Student is demonstrating consistent rubric topic mastery with minimal remediation necessary.'}
          </p>
        </div>
      </div>

      {/* Submission by Submission Breakdown */}
      <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', fontWeight: 600 }}>Question-by-Question Gap Analysis</h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {answers.map((ans) => {
          const rawGaps = ans.feedback?.missing_concepts || [];
          const gaps = rawGaps.filter((g) => g && !EXCLUDED_META.includes(g.trim().toLowerCase()));
          const hasReview = rawGaps.some((g) => g && g.trim().toLowerCase() === 'requires human review');

          return (
            <div key={ans.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <span className="badge badge-indigo">{ans.question_id}</span>
                  <span className="badge badge-purple">{ans.question?.subject}</span>
                  {hasReview && (
                    <span className="badge badge-amber" title="Requires instructor validation">
                      Requires Human Review
                    </span>
                  )}
                </div>
              </div>
              <h4 style={{ fontSize: '1rem', marginBottom: '10px' }}>{ans.question?.question_text}</h4>

              <div style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', marginBottom: '12px', fontSize: '0.9rem' }}>
                <strong>Answer:</strong> {ans.student_answer}
              </div>

              <div>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                  Missing Concepts Flagged:
                </span>
                <div style={{ marginTop: '6px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {gaps.length === 0 ? (
                    <span style={{ fontSize: '0.85rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CheckCircle size={14} /> Full conceptual rubric criteria satisfied
                    </span>
                  ) : (
                    gaps.map((g, i) => (
                      <span key={i} className="concept-tag">
                        {g}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
