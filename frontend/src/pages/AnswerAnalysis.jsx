import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import AnswerCard from '../components/AnswerCard';
import MissingConceptsCard from '../components/MissingConceptsCard';
import FeedbackPanel from '../components/FeedbackPanel';
import RecommendationCard from '../components/RecommendationCard';
import { Sparkles, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export default function AnswerAnalysis({ activeStudent }) {
  const [answers, setAnswers] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState(null);

  // Form state for analyzing or re-analyzing an answer
  const [targetQuestionId, setTargetQuestionId] = useState('');
  const [studentAnswerText, setStudentAnswerText] = useState('');
  // Marks come automatically from the assessment component - NOT from user input
  const [storedMarks, setStoredMarks] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (activeStudent) {
      loadData();
    }
  }, [activeStudent]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ansData, qData] = await Promise.all([
        apiService.getStudentAnswers(activeStudent.student_id),
        apiService.getQuestions(),
      ]);
      setAnswers(ansData);
      setQuestions(qData);

      if (ansData.length > 0) {
        handleSelectAnswer(ansData[0]);
      } else if (qData.length > 0) {
        setTargetQuestionId(qData[0].question_id);
      }
    } catch (err) {
      console.error('Failed to load answers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionChange = (newQuestionId) => {
    setTargetQuestionId(newQuestionId);
    const existing = answers.find((a) => a.question_id === newQuestionId);
    if (existing) {
      handleSelectAnswer(existing);
    } else {
      setSelectedAnswer(null);
      setStudentAnswerText('');
      setStoredMarks(null);
      setAnalysisResult(null);
    }
  };

  const handleSelectAnswer = (ans) => {
    setSelectedAnswer(ans);
    setTargetQuestionId(ans.question_id);
    setStudentAnswerText(ans.student_answer);
    // Use marks from assessment component if available; do not allow manual entry
    setStoredMarks(ans.obtained_marks !== null && ans.obtained_marks !== undefined ? ans.obtained_marks : null);

    if (ans.feedback) {
      const recs = ans.feedback.recommendations || [];
      setAnalysisResult({
        student_id: ans.student_id,
        question_id: ans.question_id,
        student_answer: ans.student_answer,
        obtained_marks: ans.obtained_marks,
        total_marks: ans.question?.total_marks || 10.0,
        ai_status: 'model_inference',
        missing_concepts: ans.feedback.missing_concepts || [],
        strengths: ans.feedback.strengths,
        weaknesses: ans.feedback.weaknesses,
        personalized_feedback: ans.feedback.personalized_feedback,
        recommendations: recs,
      });
    } else {
      setAnalysisResult(null);
    }
  };

  const handleRunAnalysis = async (e) => {
    e.preventDefault();
    if (!studentAnswerText.trim() || !targetQuestionId) {
      setNotification({ type: 'warning', text: 'Please provide both the question and the student answer.' });
      return;
    }

    setAnalyzing(true);
    setNotification(null);

    try {
      const payload = {
        student_id: activeStudent ? activeStudent.student_id : 'GUEST-01',
        question_id: targetQuestionId,
        student_answer: studentAnswerText,
        // Automatically pass existing assessment marks if available; no manual user input
        obtained_marks: storedMarks,
        save_to_db: true,
      };

      const result = await apiService.analyzeAnswer(payload);
      setAnalysisResult(result);
      if (result.obtained_marks !== null && result.obtained_marks !== undefined) {
        setStoredMarks(result.obtained_marks);
      }
      setNotification({
        type: 'success',
        text: `Analysis complete! Personalized feedback generated (${result.ai_status}).`,
      });

      // Refresh student's answers list in background
      if (activeStudent) {
        const refreshedAnswers = await apiService.getStudentAnswers(activeStudent.student_id);
        setAnswers(refreshedAnswers);
      }
    } catch (err) {
      setNotification({
        type: 'warning',
        text: `Analysis failed: ${err.response?.data?.detail || err.message}`,
      });
    } finally {
      setAnalyzing(false);
    }
  };

  if (!activeStudent) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
        <AlertCircle size={36} color="#6366f1" style={{ margin: '0 auto 12px auto' }} />
        <h3>No Student Currently Selected</h3>
        <p style={{ color: '#64748b', marginTop: '6px' }}>
          Please select a student from the top navigation or Student Selection page to view their submissions.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Student Answer Analysis</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Evaluating submissions for: <strong>{activeStudent.student_name}</strong> ({activeStudent.student_id})
          </p>
        </div>
        <button className="btn btn-outline" onClick={loadData}>
          <RefreshCw size={16} />
          <span>Refresh Answers</span>
        </button>
      </div>

      {notification && (
        <div className={`alert ${notification.type === 'success' ? 'alert-success' : 'alert-warning'}`}>
          {notification.text}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.3fr', gap: '24px' }}>
        {/* Left Column: Existing Submissions */}
        <div>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '14px', fontWeight: 600 }}>
            Submissions ({answers.length})
          </h3>

          {loading ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>Loading submissions...</div>
          ) : answers.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
              No answers submitted yet for this student. Use the evaluation editor on the right to input and analyze one.
            </div>
          ) : (
            <div>
              {answers.map((ans) => (
                <AnswerCard
                  key={ans.id}
                  answer={ans}
                  isSelected={selectedAnswer?.id === ans.id}
                  onAnalyzeClick={handleSelectAnswer}
                />
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Interactive Evaluation Workspace */}
        <div>
          <div className="card" style={{ marginBottom: '20px' }}>
            <div className="card-header">
              <h3 className="card-title">
                <Sparkles size={18} color="#4f46e5" />
                <span>AI Evaluation & Feedback Workspace</span>
              </h3>
              <span className="badge badge-indigo">
                {selectedAnswer ? `Editing: ${selectedAnswer.question_id}` : 'New Analysis'}
              </span>
            </div>

            <form onSubmit={handleRunAnalysis}>
              <div className="form-group">
                <label className="form-label">Assessment Question</label>
                <select
                  className="form-control"
                  value={targetQuestionId}
                  onChange={(e) => handleQuestionChange(e.target.value)}
                  required
                >
                  <option value="">Select a Question...</option>
                  {questions.map((q) => (
                    <option key={q.question_id} value={q.question_id}>
                      {q.question_id} - {q.question_text.slice(0, 65)}...
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Student Written Answer</label>
                <textarea
                  className="form-control"
                  rows={5}
                  placeholder="Paste or write the student's short-answer response here..."
                  value={studentAnswerText}
                  onChange={(e) => setStudentAnswerText(e.target.value)}
                  required
                />
              </div>

              {/* Assessment marks status - read only, sourced from assessment component */}
              <div className="form-group">
                <div
                  style={{
                    padding: '10px 14px',
                    borderRadius: '8px',
                    backgroundColor: storedMarks !== null ? '#f0fdf4' : '#fef9c3',
                    border: storedMarks !== null ? '1px solid #bbf7d0' : '1px solid #fde68a',
                    fontSize: '0.84rem',
                    color: storedMarks !== null ? '#065f46' : '#92400e',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  {storedMarks !== null ? (
                    <>
                      <CheckCircle2 size={15} />
                      <span>Assessment marks: <strong>{storedMarks} marks</strong> (provided by assessment component)</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle size={15} />
                      <span>Assessment marks not yet available.</span>
                    </>
                  )}
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center' }}
                disabled={analyzing}
              >
                {analyzing ? (
                  <>
                    <RefreshCw size={16} className="spin" />
                    <span>Analyzing with AI...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={16} />
                    <span>Generate Personalized Feedback</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Analysis Results Display */}
          {analysisResult && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <MissingConceptsCard
                missingConcepts={analysisResult.missing_concepts}
                aiStatus={analysisResult.ai_status}
              />

              <FeedbackPanel
                feedback={{
                  strengths: analysisResult.strengths,
                  weaknesses: analysisResult.weaknesses,
                  personalized_feedback: analysisResult.personalized_feedback,
                }}
              />

              {analysisResult.recommendations && analysisResult.recommendations.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">Curated Learning Recommendations</h3>
                    <span className="badge badge-emerald">Verified Resources</span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                    {analysisResult.recommendations.map((rec, idx) => (
                      <RecommendationCard key={idx} recommendation={rec} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
