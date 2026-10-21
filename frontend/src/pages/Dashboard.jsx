import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import {
  Users, FileQuestion, BookOpen, AlertTriangle, UploadCloud,
  RefreshCw, Brain, CheckCircle2, TrendingDown, BookMarked,
  Lightbulb, Target, BarChart2, GitMerge, ArrowRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const COLORS = {
  identified: '#10b981',
  missing: '#f43f5e',
  expected: '#6366f1',
  high: '#f43f5e',
  medium: '#f59e0b',
  low: '#6366f1',
};

const PRIORITY_COLORS = {
  High: '#f43f5e',
  Medium: '#f59e0b',
  Low: '#6366f1',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'white',
        border: '1px solid #e2e8f0',
        borderRadius: '8px',
        padding: '10px 14px',
        fontSize: '0.82rem',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      }}>
        <p style={{ fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color || p.fill, margin: '2px 0' }}>
            {p.name}: <strong>{p.value}</strong>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard({ activeStudent, onSelectStudent }) {
  const navigate = useNavigate();
  const [studentsList, setStudentsList] = useState([]);
  const [dashStats, setDashStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Load students roster for quick switcher
  useEffect(() => {
    let isMounted = true;
    apiService.getStudents()
      .then((data) => {
        if (isMounted && data) {
          setStudentsList(data);
          if (!activeStudent && data.length > 0 && onSelectStudent) {
            onSelectStudent(data[0]);
          }
        }
      })
      .catch((err) => console.error('Failed to load students roster:', err));

    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch real student dashboard statistics whenever activeStudent changes
  useEffect(() => {
    let isMounted = true;

    if (!activeStudent?.student_id) {
      setDashStats(null);
      setLoading(false);
      return;
    }

    // Requirement 4.5: Clear previous student data during loading
    setDashStats(null);
    setLoading(true);

    apiService.getDashboardStats(activeStudent.student_id)
      .then((data) => {
        // Requirement 4.7: Prevent displaying data belonging to another student
        if (isMounted && data && data.student_id === activeStudent.student_id) {
          setDashStats(data);
        }
      })
      .catch((err) => {
        if (isMounted) {
          console.error(`Failed to load dashboard for student ${activeStudent.student_id}:`, err);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeStudent?.student_id]);

  const handleRefresh = async () => {
    if (!activeStudent?.student_id) return;
    setLoading(true);
    setDashStats(null);
    try {
      const data = await apiService.getDashboardStats(activeStudent.student_id);
      if (data && data.student_id === activeStudent.student_id) {
        setDashStats(data);
      }
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      setUploadStatus('Uploading & validating CSV...');
      const res = await apiService.uploadDataset(file);
      setUploadStatus(res.message);
      handleRefresh();
    } catch (err) {
      setUploadStatus(`Error: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleSeedDemo = async () => {
    try {
      setUploadStatus('Seeding academic benchmark dataset...');
      const res = await apiService.seedDemoData();
      setUploadStatus(res.message);
      handleRefresh();
    } catch (err) {
      setUploadStatus('Failed to seed dataset.');
    }
  };

  const summary = dashStats?.summary || {};
  const questionCoverage = dashStats?.question_coverage || [];
  const gapDistribution = dashStats?.gap_distribution || [];
  const priorityDistribution = dashStats?.priority_distribution || [];
  const identifiedConcepts = dashStats?.identified_concepts || [];
  const missingConcepts = dashStats?.missing_concepts || [];
  const expectedUndetectedConcepts = dashStats?.expected_undetected_concepts || missingConcepts;
  const rootKnowledgeGaps = dashStats?.root_knowledge_gaps || [];

  // Chart 1: Concept Understanding (Identified vs Expected but Undetected)
  const conceptChartData = [
    {
      name: 'Correctly Identified',
      value: identifiedConcepts.length,
      fill: COLORS.identified,
    },
    {
      name: 'Expected Undetected',
      value: expectedUndetectedConcepts.length,
      fill: COLORS.missing,
    },
  ];

  // Chart 2: Knowledge Gap Distribution across 5 OOP topics
  const defaultGapTopics = [
    'Classes and Objects',
    'Inheritance',
    'Method Overriding',
    'Static and Instance Variables',
    'Exception Handling',
  ];
  const gapChartData = defaultGapTopics.map((topicName) => {
    const found = gapDistribution.find((g) => g.topic === topicName);
    return {
      topic: topicName,
      missing_count: found ? found.missing_count : 0,
    };
  });

  // Chart 3: Recommendation Priorities
  const priorityChartData = [
    { priority: 'High', count: priorityDistribution.find((p) => p.priority === 'High')?.count || 0 },
    { priority: 'Medium', count: priorityDistribution.find((p) => p.priority === 'Medium')?.count || 0 },
    { priority: 'Low', count: priorityDistribution.find((p) => p.priority === 'Low')?.count || 0 },
  ];

  return (
    <div>
      {/* Header & Quick Student Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>Student Dashboard</span>
            {activeStudent && (
              <span className="badge badge-indigo" style={{ fontSize: '0.88rem', padding: '4px 10px' }}>
                {activeStudent.student_name} ({activeStudent.student_id})
              </span>
            )}
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '4px 0 0 0' }}>
            RubriMark AI: Real-Time Student-Specific Knowledge Gap & Explainable Feedback Dashboard
          </p>
        </div>

        {/* Action Controls & Quick Student Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {studentsList.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="student-quick-switch" style={{ fontSize: '0.82rem', fontWeight: 600, color: '#475569' }}>
                Active Student:
              </label>
              <select
                id="student-quick-switch"
                className="form-control"
                style={{ padding: '6px 10px', fontSize: '0.85rem', fontWeight: 600, minWidth: '180px' }}
                value={activeStudent?.student_id || ''}
                onChange={(e) => {
                  const selected = studentsList.find((s) => s.student_id === e.target.value);
                  if (selected && onSelectStudent) {
                    onSelectStudent(selected);
                  }
                }}
              >
                {studentsList.map((s) => (
                  <option key={s.student_id} value={s.student_id}>
                    {s.student_id} — {s.student_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button className="btn btn-outline" style={{ padding: '7px 12px', fontSize: '0.82rem' }} onClick={() => navigate('/students')}>
            <Users size={14} />
            <span>Roster</span>
          </button>
          <button className="btn btn-primary" style={{ padding: '7px 14px', fontSize: '0.82rem' }} onClick={handleRefresh}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {uploadStatus && (
        <div className="alert alert-info" style={{ marginBottom: '16px' }}>{uploadStatus}</div>
      )}

      {/* Empty State: No Student Selected */}
      {!activeStudent ? (
        <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
          <Users size={40} color="#6366f1" style={{ margin: '0 auto 12px' }} />
          <h3>No Student Selected</h3>
          <p style={{ color: '#64748b' }}>Select a registered student from the roster to view their dynamic AI dashboard.</p>
          <button className="btn btn-primary" style={{ margin: '16px auto 0', display: 'inline-flex' }} onClick={() => navigate('/students')}>
            Go to Student Selection
          </button>
        </div>
      ) : loading ? (
        /* Loading State: Cleared previous data during loading */
        <div className="card" style={{ padding: '70px 20px', textAlign: 'center', color: '#64748b' }}>
          <Brain size={36} color="#6366f1" style={{ margin: '0 auto 12px', display: 'block', animation: 'pulse 1.5s infinite' }} />
          <h3 style={{ fontSize: '1.15rem', color: '#1e293b', marginBottom: '6px' }}>
            Loading Authentic Assessment Data...
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#64748b' }}>
            Fetching AI analysis results, model-identified concepts, and curriculum records for <strong>{activeStudent.student_name}</strong> ({activeStudent.student_id}).
          </p>
        </div>
      ) : (
        <>
          {/* SECTION 2: Dynamic Student-Specific Dashboard Statistics (6 Cards) */}
          <div className="stats-grid" style={{ marginBottom: '24px' }}>
            {/* Card 1: Questions Answered */}
            <div className="stat-card" id="card-questions-answered">
              <div className="stat-info">
                <h4>Questions Answered</h4>
                <div className="stat-value">{summary.questions_answered ?? summary.total_answers ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  Assessed OOP questions (Q1–Q5)
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#e0e7ff', color: '#4f46e5' }}>
                <FileQuestion size={24} />
              </div>
            </div>

            {/* Card 2: Concepts Identified */}
            <div className="stat-card" id="card-concepts-identified">
              <div className="stat-info">
                <h4>Concepts Identified</h4>
                <div className="stat-value">{summary.concepts_identified ?? summary.total_identified_concepts ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  Correctly demonstrated concepts
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#d1fae5', color: '#059669' }}>
                <CheckCircle2 size={24} />
              </div>
            </div>

            {/* Card 3: Missing Concepts */}
            <div className="stat-card" id="card-missing-concepts">
              <div className="stat-info">
                <h4>Missing Concepts</h4>
                <div className="stat-value">{summary.missing_concepts ?? summary.total_missing_concepts ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  Knowledge gaps detected
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#fee2e2', color: '#dc2626' }}>
                <TrendingDown size={24} />
              </div>
            </div>

            {/* Card 4: Root Knowledge Gaps (Concept Dependency Analysis) */}
            <div className="stat-card" id="card-root-knowledge-gaps">
              <div className="stat-info">
                <h4>Root Knowledge Gaps</h4>
                <div className="stat-value" style={{ color: (summary.root_knowledge_gaps ?? 0) > 0 ? '#e11d48' : '#059669' }}>
                  {summary.root_knowledge_gaps ?? summary.root_gaps_count ?? 0}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  Foundational DAG bottlenecks
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#ffe4e6', color: '#e11d48' }}>
                <GitMerge size={24} />
              </div>
            </div>

            {/* Card 5: Personalized Feedback Records */}
            <div className="stat-card" id="card-feedback-records">
              <div className="stat-info">
                <h4>Personalized Feedback Records</h4>
                <div className="stat-value">{summary.personalized_feedback_records ?? summary.total_feedback_records ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  AI Status: <strong style={{ color: summary.ai_analysis_status === 'completed' ? '#059669' : '#f59e0b' }}>
                    {summary.ai_analysis_status === 'completed' ? 'Completed' : 'Pending'}
                  </strong>
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#ede9fe', color: '#7c3aed' }}>
                <Brain size={24} />
              </div>
            </div>

            {/* Card 6: Learning Recommendations */}
            <div className="stat-card" id="card-learning-recommendations">
              <div className="stat-info">
                <h4>Learning Recommendations</h4>
                <div className="stat-value">{summary.learning_recommendations ?? summary.total_recommendations ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '2px' }}>
                  SLIIT IT2030 lecture materials
                </div>
              </div>
              <div className="stat-icon" style={{ backgroundColor: '#fef3c7', color: '#d97706' }}>
                <BookMarked size={24} />
              </div>
            </div>
          </div>

          {/* SECTION 3: Dashboard Charts (Row 1) */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>

            {/* Chart 1: Concept Understanding (Identified vs Expected Undetected) */}
            <div className="card" id="chart-concept-understanding">
              <div className="card-header">
                <h3 className="card-title">
                  <CheckCircle2 size={18} color="#10b981" />
                  <span>Chart 1 – Concept Understanding</span>
                </h3>
                <span className="badge badge-emerald">AI Assessment</span>
              </div>

              {identifiedConcepts.length === 0 && expectedUndetectedConcepts.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
                  No concept evaluation data available for this student.
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
                  <div style={{ width: '190px', height: '190px', flexShrink: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={conceptChartData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={75}
                          paddingAngle={3}
                        >
                          {conceptChartData.map((entry, i) => (
                            <Cell key={i} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div style={{ flex: 1, minWidth: '220px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: COLORS.identified, display: 'inline-block' }}></span>
                          Correctly Identified:
                        </span>
                        <strong style={{ color: '#059669', fontSize: '0.95rem' }}>{identifiedConcepts.length}</strong>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
                          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: COLORS.missing, display: 'inline-block' }}></span>
                          Expected but Undetected:
                        </span>
                        <strong style={{ color: '#dc2626', fontSize: '0.95rem' }}>{expectedUndetectedConcepts.length}</strong>
                      </div>
                    </div>

                    {/* Breakdown details */}
                    {rootKnowledgeGaps.length > 0 && (
                      <div style={{ backgroundColor: '#fff1f2', border: '1px solid #fecdd3', borderRadius: '6px', padding: '8px 10px', marginBottom: '10px' }}>
                        <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#be123c', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <GitMerge size={13} />
                          <span>Root-Cause Bottlenecks ({rootKnowledgeGaps.length}):</span>
                        </div>
                        <ul style={{ margin: '4px 0 0 0', paddingLeft: '18px', fontSize: '0.76rem', color: '#9f1239' }}>
                          {rootKnowledgeGaps.map((rg, idx) => (
                            <li key={idx}><strong>{rg}</strong></li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {missingConcepts.length > 0 && (
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                        <span style={{ fontWeight: 600 }}>Detected Gaps: </span>
                        {missingConcepts.slice(0, 3).join(', ')}
                        {missingConcepts.length > 3 && ` +${missingConcepts.length - 3} more`}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Chart 2: Knowledge Gap Distribution (5 OOP Topics) */}
            <div className="card" id="chart-gap-distribution">
              <div className="card-header">
                <h3 className="card-title">
                  <AlertTriangle size={18} color="#f43f5e" />
                  <span>Chart 2 – Knowledge Gap Distribution</span>
                </h3>
                <span className="badge badge-rose">By OOP Topic</span>
              </div>

              <div style={{ width: '100%', height: '220px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={gapChartData} layout="vertical" margin={{ top: 8, right: 24, left: 20, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" allowDecimals={false} tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="topic" width={160} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="missing_count" name="Missing Concepts" fill="#f43f5e" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* SECTION 3: Dashboard Charts (Row 2) */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.3fr', gap: '24px', marginBottom: '24px' }}>

            {/* Chart 3: Recommendation Priorities (High, Medium, Low) */}
            <div className="card" id="chart-recommendation-priorities">
              <div className="card-header">
                <h3 className="card-title">
                  <Lightbulb size={18} color="#f59e0b" />
                  <span>Chart 3 – Recommendation Priorities</span>
                </h3>
                <span className="badge badge-amber">Learning Remediation</span>
              </div>

              {priorityChartData.every((p) => p.count === 0) ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
                  No learning recommendations currently assigned.
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '20px', flexWrap: 'wrap' }}>
                  <div style={{ width: '170px', height: '170px', flexShrink: 0 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={priorityChartData}
                          dataKey="count"
                          nameKey="priority"
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={75}
                          paddingAngle={3}
                        >
                          {priorityChartData.map((entry, i) => (
                            <Cell key={i} fill={PRIORITY_COLORS[entry.priority] || '#6366f1'} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div style={{ flex: 1, minWidth: '160px', fontSize: '0.84rem' }}>
                    {priorityChartData.map((p, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: PRIORITY_COLORS[p.priority], display: 'inline-block' }}></span>
                          <span>{p.priority} Priority:</span>
                        </span>
                        <strong style={{ color: PRIORITY_COLORS[p.priority] }}>{p.count}</strong>
                      </div>
                    ))}
                    <button
                      className="btn btn-outline"
                      style={{ padding: '6px 12px', fontSize: '0.8rem', marginTop: '8px', width: '100%', justifyContent: 'center' }}
                      onClick={() => navigate('/recommendations')}
                    >
                      <BookOpen size={14} />
                      <span>View All Recommendations</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Chart 4 – Question-Wise Concept Coverage (Q1–Q5) */}
            <div className="card" id="chart-question-coverage">
              <div className="card-header">
                <h3 className="card-title">
                  <Target size={18} color="#6366f1" />
                  <span>Chart 4 – Question-Wise Concept Coverage</span>
                </h3>
                <span className="badge badge-indigo">Standardized Q1–Q5</span>
              </div>

              {questionCoverage.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#94a3b8' }}>
                  No question-wise analysis data available.
                </div>
              ) : (
                <div style={{ width: '100%', height: '230px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={questionCoverage} margin={{ top: 8, right: 16, left: -10, bottom: 4 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="question" tick={{ fontSize: 12, fontWeight: 700 }} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '0.8rem' }} />
                      <Bar dataKey="expected" name="Expected Concepts" fill="#6366f1" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="identified" name="Identified Concepts" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="missing" name="Missing Concepts" fill="#f43f5e" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          {/* Quick Module Navigation Links */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
            {[
              { label: 'Answer Analysis', path: '/analysis', icon: <BarChart2 size={18} />, color: '#6366f1' },
              { label: 'Knowledge Gaps', path: '/knowledge-gaps', icon: <AlertTriangle size={18} />, color: '#f43f5e' },
              { label: 'Concept Dependencies', path: '/concept-dependencies', icon: <GitMerge size={18} />, color: '#f59e0b' },
              { label: 'Personalized Feedback', path: '/feedback', icon: <Brain size={18} />, color: '#7c3aed' },
              { label: 'Recommendations', path: '/recommendations', icon: <BookMarked size={18} />, color: '#059669' },
              { label: 'Feedback History', path: '/history', icon: <BookOpen size={18} />, color: '#0284c7' },
            ].map((item) => (
              <button
                key={item.path}
                className="btn btn-outline"
                style={{ justifyContent: 'flex-start', padding: '12px 14px', gap: '10px', fontWeight: 600 }}
                onClick={() => navigate(item.path)}
              >
                <span style={{ color: item.color }}>{item.icon}</span>
                <span style={{ fontSize: '0.84rem' }}>{item.label}</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
