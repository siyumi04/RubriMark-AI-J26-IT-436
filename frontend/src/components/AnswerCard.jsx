import React from 'react';
import MarksSummary from './MarksSummary';
import { BookOpen, Calendar, HelpCircle } from 'lucide-react';

export default function AnswerCard({ answer, onAnalyzeClick, isSelected }) {
  const { question, student_answer, obtained_marks, submission_date } = answer;
  const formattedDate = submission_date
    ? new Date(submission_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Recent';

  return (
    <div
      className="card"
      style={{
        border: isSelected ? '2px solid #6366f1' : '1px solid #e2e8f0',
        marginBottom: '16px',
      }}
    >
      <div className="card-header" style={{ marginBottom: '12px' }}>
        <div>
          <span className="badge badge-indigo" style={{ marginRight: '8px' }}>
            {answer.question_id}
          </span>
          <span className="badge badge-purple">
            {question?.subject || 'Subject Domain'}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#64748b' }}>
          <Calendar size={14} />
          <span>{formattedDate}</span>
        </div>
      </div>

      <div style={{ marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
          <HelpCircle size={18} color="#4f46e5" style={{ flexShrink: 0, marginTop: '2px' }} />
          <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#1e293b' }}>
            {question?.question_text || `Question ${answer.question_id}`}
          </h4>
        </div>
      </div>

      <div
        style={{
          backgroundColor: '#f8fafc',
          padding: '16px',
          borderRadius: '8px',
          borderLeft: '4px solid #6366f1',
          marginBottom: '16px',
        }}
      >
        <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', marginBottom: '6px', fontWeight: 600 }}>
          Submitted Student Answer
        </div>
        <p style={{ fontSize: '0.94rem', color: '#1e293b', whiteSpace: 'pre-wrap' }}>
          {student_answer}
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <MarksSummary
          obtainedMarks={obtained_marks}
          totalMarks={question?.total_marks || 10.0}
        />

        {onAnalyzeClick && (
          <button
            className="btn btn-primary"
            onClick={() => onAnalyzeClick(answer)}
          >
            Review & Analyze Answer
          </button>
        )}
      </div>
    </div>
  );
}
