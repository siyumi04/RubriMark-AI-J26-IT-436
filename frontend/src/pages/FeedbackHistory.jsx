import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { History, Calendar, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

export default function FeedbackHistory({ activeStudent }) {
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (activeStudent) {
      loadHistory();
    }
  }, [activeStudent]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await apiService.getStudentFeedback(activeStudent.student_id);
      setHistoryItems(data);
    } catch (err) {
      console.error('Failed to load feedback history:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedId(expandedId === id ? null : id);
  };

  if (!activeStudent) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
        <History size={36} color="#6366f1" style={{ margin: '0 auto 12px auto' }} />
        <h3>No Student Selected</h3>
        <p style={{ color: '#64748b' }}>Please select a student to view their complete assessment feedback history.</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Feedback Assessment History & Audit Log</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Historical timeline of generated feedback evaluations for <strong>{activeStudent.student_name}</strong>
          </p>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading historical entries...</div>
      ) : historyItems.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          No feedback entries recorded in the audit log for this student.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {historyItems.map((item) => {
            const isExpanded = expandedId === item.feedback_id;
            const dateStr = item.created_at
              ? new Date(item.created_at).toLocaleString('en-US', {
                  dateStyle: 'medium',
                  timeStyle: 'short',
                })
              : 'Recorded';

            return (
              <div key={item.feedback_id} className="card" style={{ padding: 0 }}>
                <div
                  style={{
                    padding: '18px 24px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    backgroundColor: isExpanded ? '#f8fafc' : '#ffffff',
                    borderTopLeftRadius: '12px',
                    borderTopRightRadius: '12px',
                  }}
                  onClick={() => toggleExpand(item.feedback_id)}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span className="badge badge-indigo">{item.question_id}</span>
                    <div>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>
                        {item.question_text || `Question ${item.question_id}`}
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                        <Calendar size={12} />
                        <span>{dateStr}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {item.requires_human_review && (
                      <span className="badge badge-amber" title="Requires instructor verification">
                        Requires Human Review
                      </span>
                    )}
                    <span className="badge badge-emerald">
                      {item.obtained_marks !== null ? `${item.obtained_marks}/${item.total_marks || 10} Marks` : 'Pending Score'}
                    </span>
                    <span className="badge badge-rose">
                      {item.missing_concepts ? item.missing_concepts.length : 0} Gaps
                    </span>
                    {isExpanded ? <ChevronUp size={18} color="#64748b" /> : <ChevronDown size={18} color="#64748b" />}
                  </div>
                </div>

                {isExpanded && (
                  <div style={{ padding: '24px', borderTop: '1px solid #e2e8f0' }}>
                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                        Submitted Student Answer
                      </div>
                      <p style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', fontSize: '0.9rem', color: '#1e293b' }}>
                        {item.student_answer}
                      </p>
                    </div>

                    <div style={{ marginBottom: '16px' }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '4px' }}>
                        Generated Personalized Feedback
                      </div>
                      <p style={{ fontSize: '0.9rem', color: '#1e293b', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                        {item.personalized_feedback}
                      </p>
                    </div>

                    {item.missing_concepts && item.missing_concepts.length > 0 && (
                      <div>
                        <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', marginBottom: '6px' }}>
                          Identified Knowledge Gaps
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {item.missing_concepts.map((g, i) => (
                            <span key={i} className="concept-tag">{g}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
