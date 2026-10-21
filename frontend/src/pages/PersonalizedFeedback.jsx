import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import FeedbackPanel from '../components/FeedbackPanel';
import MarksSummary from '../components/MarksSummary';
import { MessageSquareText, Calendar, BookOpen } from 'lucide-react';

export default function PersonalizedFeedback({ activeStudent }) {
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeStudent) {
      loadFeedback();
    }
  }, [activeStudent]);

  const loadFeedback = async () => {
    setLoading(true);
    try {
      const data = await apiService.getStudentFeedback(activeStudent.student_id);
      setFeedbacks(data);
    } catch (err) {
      console.error('Failed to load feedback:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!activeStudent) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
        <MessageSquareText size={36} color="#6366f1" style={{ margin: '0 auto 12px auto' }} />
        <h3>No Student Selected</h3>
        <p style={{ color: '#64748b' }}>Please select a student to view personalized academic feedback.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Personalized Feedback Repository</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Tailored assessment evaluations for <strong>{activeStudent.student_name}</strong> ({activeStudent.student_id})
          </p>
        </div>
        <span className="badge badge-purple" style={{ fontSize: '0.85rem' }}>
          {feedbacks.length} Synthesized Feedback Reports
        </span>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading feedback reports...</div>
      ) : feedbacks.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          No feedback reports recorded yet for this student. Navigate to Answer Analysis to evaluate an answer.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {feedbacks.map((fb) => (
            <div key={fb.feedback_id} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="badge badge-indigo">{fb.question_id}</span>
                  <span style={{ fontWeight: 600, fontSize: '1rem', color: '#0f172a' }}>
                    {fb.question_text || `Question ${fb.question_id}`}
                  </span>
                  {fb.requires_human_review && (
                    <span className="badge badge-amber" title="Flagged by AI model as needing instructor verification">
                      Requires Human Review
                    </span>
                  )}
                </div>
                <MarksSummary obtainedMarks={fb.obtained_marks} totalMarks={fb.total_marks || 10.0} />
              </div>

              {fb.student_answer && (
                <div
                  style={{
                    backgroundColor: '#f8fafc',
                    padding: '14px 18px',
                    borderRadius: '8px',
                    borderLeft: '4px solid #6366f1',
                    fontSize: '0.9rem',
                    color: '#1e293b'
                  }}
                >
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Evaluated Student Answer
                  </div>
                  <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{fb.student_answer}</p>
                </div>
              )}

              <FeedbackPanel
                feedback={{
                  strengths: fb.strengths,
                  weaknesses: fb.weaknesses,
                  personalized_feedback: fb.personalized_feedback,
                }}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
