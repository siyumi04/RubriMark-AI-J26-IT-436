import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import {
  GitMerge,
  Network,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  ArrowRight,
  TrendingUp,
  Layers,
  Sparkles,
  BookOpen,
  ShieldAlert,
  ChevronRight,
  Info
} from 'lucide-react';

export default function ConceptDependencyAnalysis({ activeStudent }) {
  const [dependencyData, setDependencyData] = useState(null);
  const [curriculumData, setCurriculumData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeTab, setActiveTab] = useState('student'); // 'student' | 'curriculum'

  useEffect(() => {
    loadData();
  }, [activeStudent]);

  const loadData = async () => {
    setLoading(true);
    try {
      const curr = await apiService.getCurriculumDependencies();
      setCurriculumData(curr);

      if (activeStudent) {
        const studentDep = await apiService.getStudentDependencies(activeStudent.student_id);
        setDependencyData(studentDep);
      }
    } catch (err) {
      console.error('Failed to load Concept Dependency data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'root_cause':
        return <span className="badge badge-rose" style={{ animation: 'pulse 2s infinite' }}>Root-Cause Gap</span>;
      case 'missing':
        return <span className="badge badge-amber">Missing Concept</span>;
      case 'at_risk':
        return <span className="badge badge-indigo">At-Risk Downstream</span>;
      case 'mastered':
      default:
        return <span className="badge badge-emerald">Mastered</span>;
    }
  };

  const getDifficultyBadge = (difficulty) => {
    switch (difficulty) {
      case 'Foundational':
        return <span className="badge badge-emerald">Foundational</span>;
      case 'Core':
        return <span className="badge badge-indigo">Core</span>;
      case 'Advanced':
        return <span className="badge badge-rose">Advanced</span>;
      default:
        return <span className="badge badge-slate">{difficulty}</span>;
    }
  };

  const nodesToDisplay = activeTab === 'student' && dependencyData
    ? dependencyData.graph_nodes
    : curriculumData?.nodes || [];

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-indigo" style={{ fontWeight: 600 }}>
              Concept Dependency Framework
            </span>
            <span className="badge badge-slate">OOP Curriculum DAG</span>
          </div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Concept Dependency & Prerequisite DAG Analysis</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Hierarchical prerequisite reasoning to isolate root-cause knowledge bottlenecks and structure targeted remediation.
          </p>
        </div>

        {/* View Toggle */}
        <div style={{ display: 'flex', background: '#f1f5f9', borderRadius: '8px', padding: '4px' }}>
          <button
            className={`btn btn-sm ${activeTab === 'student' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('student')}
            disabled={!activeStudent}
          >
            Student Diagnostics
          </button>
          <button
            className={`btn btn-sm ${activeTab === 'curriculum' ? 'btn-primary' : 'btn-ghost'}`}
            onClick={() => setActiveTab('curriculum')}
          >
            Curriculum DAG
          </button>
        </div>
      </div>

      {/* Metrics Row (for active student) */}
      {activeTab === 'student' && dependencyData && (
        <div className="stats-grid" style={{ marginBottom: '24px' }}>
          <div className="stat-card">
            <div className="stat-icon emerald">
              <TrendingUp size={22} />
            </div>
            <div className="stat-info">
              <h3>{dependencyData.mastery_rate}%</h3>
              <p>Curriculum Mastery Rate</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon rose">
              <ShieldAlert size={22} />
            </div>
            <div className="stat-info">
              <h3>{dependencyData.root_causes.length}</h3>
              <p>Root-Cause Bottlenecks</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon amber">
              <AlertTriangle size={22} />
            </div>
            <div className="stat-info">
              <h3>{dependencyData.missing_concepts_count}</h3>
              <p>Total Flagged Gaps</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon indigo">
              <Layers size={22} />
            </div>
            <div className="stat-info">
              <h3>{dependencyData.at_risk_concepts.length}</h3>
              <p>At-Risk Downstream Topics</p>
            </div>
          </div>
        </div>
      )}

      {/* Academic Summary Alert */}
      {activeTab === 'student' && dependencyData && (
        <div className={`alert ${dependencyData.root_causes.length > 0 ? 'alert-warning' : 'alert-info'}`} style={{ marginBottom: '24px' }}>
          <Network size={22} style={{ flexShrink: 0 }} />
          <div>
            <strong>Concept Dependency Diagnostic:</strong> {dependencyData.academic_summary}
            <div style={{ marginTop: '6px', fontSize: '0.85rem', opacity: 0.9 }}>
              Student: <strong>{dependencyData.student?.student_name}</strong> ({dependencyData.student?.student_id}) &bull; {dependencyData.student?.answers_submitted} Assessed Answers Analyzed
            </div>
          </div>
        </div>
      )}

      {/* Root Cause vs Downstream At-Risk Section */}
      {activeTab === 'student' && dependencyData && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
          {/* Primary Root Causes */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={18} color="#f43f5e" />
                <h3 className="card-title">Primary Root-Cause Gaps</h3>
              </div>
              <span className="badge badge-rose">{dependencyData.root_causes.length} Foundational</span>
            </div>

            {dependencyData.root_causes.length === 0 ? (
              <div style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 0' }}>
                <CheckCircle size={18} />
                <span>No foundational prerequisite bottlenecks identified. Student possesses sound core knowledge!</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {dependencyData.root_causes.map((rc, idx) => (
                  <div key={idx} style={{ padding: '12px', background: '#fff1f2', borderRadius: '8px', border: '1px solid #fecdd3' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <strong style={{ color: '#9f1239' }}>{rc.concept}</strong>
                      <span className="badge badge-rose">{rc.module}</span>
                    </div>
                    <p style={{ fontSize: '0.82rem', color: '#881337', marginBottom: '8px' }}>{rc.description}</p>
                    <div style={{ fontSize: '0.8rem', color: '#be123c' }}>
                      <strong>Triggers Downstream Failures In:</strong> {rc.caused_downstream_gaps.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* At-Risk Downstream Topics */}
          <div className="card">
            <div className="card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertTriangle size={18} color="#6366f1" />
                <h3 className="card-title">Downstream Vulnerabilities (At-Risk)</h3>
              </div>
              <span className="badge badge-indigo">{dependencyData.at_risk_concepts.length} Concepts</span>
            </div>

            {dependencyData.at_risk_concepts.length === 0 ? (
              <div style={{ color: '#059669', display: 'flex', alignItems: 'center', gap: '8px', padding: '12px 0' }}>
                <CheckCircle size={18} />
                <span>No downstream concepts are at risk of misconception due to prerequisite gaps.</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {dependencyData.at_risk_concepts.map((ar, idx) => (
                  <div key={idx} style={{ padding: '12px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <strong>{ar.concept}</strong>
                      <span className="badge badge-indigo">{ar.module}</span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      <strong>Prerequisite Barrier:</strong> Blocked because prerequisite <em>'{ar.blocked_by.join(', ')}'</em> is unmastered.
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Topologically Ordered Remediation Learning Path */}
      {activeTab === 'student' && dependencyData && dependencyData.remediation_learning_path.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BookOpen size={18} color="#2563eb" />
              <h3 className="card-title">Topologically Sorted Remediation Sequence (Prerequisite-First)</h3>
            </div>
            <span className="badge badge-indigo">Remediation Path</span>
          </div>

          <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: '16px' }}>
            To maximize learning retention, concepts must be reviewed in strict prerequisite order. Resolving Step 1 unblocks comprehension for subsequent topics.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '12px' }}>
            {dependencyData.remediation_learning_path.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: '14px',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  background: '#ffffff',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <div
                      style={{
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        background: '#2563eb',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.8rem',
                        fontWeight: 700
                      }}
                    >
                      {item.step}
                    </div>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>{item.concept}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5, marginBottom: '8px' }}>
                    {item.description}
                  </p>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '8px' }}>
                  <span className="badge badge-slate">{item.module}</span>
                  {getDifficultyBadge(item.difficulty)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interactive Concept Dependency DAG Visualization Grid */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={18} color="#4f46e5" />
            <h3 className="card-title">
              {activeTab === 'student' ? 'Student Concept Mastery Graph (DAG)' : 'Full OOP Curriculum Dependency DAG'}
            </h3>
          </div>
          <div style={{ display: 'flex', gap: '6px' }}>
            <span className="badge badge-emerald">Mastered</span>
            <span className="badge badge-rose">Root-Cause</span>
            <span className="badge badge-amber">Missing</span>
            <span className="badge badge-indigo">At-Risk</span>
          </div>
        </div>

        <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '20px' }}>
          Select any concept node to inspect its formal theoretical definition, prerequisite chain, and associated assessment question.
        </p>

        {/* Nodes Grid organized by Curriculum Modules */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
          {nodesToDisplay.map((node) => {
            const isSelected = selectedNode?.id === node.id;
            return (
              <div
                key={node.id}
                onClick={() => setSelectedNode(node)}
                style={{
                  padding: '16px',
                  borderRadius: '10px',
                  border: isSelected ? '2px solid #2563eb' : '1px solid #e2e8f0',
                  background: isSelected ? '#eff6ff' : '#ffffff',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected ? '0 4px 12px rgba(37,99,235,0.15)' : 'none'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 600 }}>{node.module} ({node.question_id})</span>
                  {getStatusBadge(node.status)}
                </div>

                <h4 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b', marginBottom: '6px' }}>
                  {node.label}
                </h4>

                <p style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.5, marginBottom: '12px' }}>
                  {node.description}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {getDifficultyBadge(node.difficulty)}
                  <span style={{ fontSize: '0.78rem', color: '#2563eb', display: 'flex', alignItems: 'center', gap: '2px' }}>
                    Inspect Details <ChevronRight size={14} />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Node Details Drawer/Card */}
      {selectedNode && (
        <div className="card" style={{ marginTop: '24px', borderLeft: '4px solid #2563eb' }}>
          <div className="card-header">
            <div>
              <span className="badge badge-indigo">{selectedNode.module}</span>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginTop: '6px' }}>{selectedNode.label}</h3>
            </div>
            <button className="btn btn-sm btn-outline" onClick={() => setSelectedNode(null)}>Close</button>
          </div>

          <p style={{ fontSize: '0.9rem', color: '#334155', lineHeight: 1.6, marginBottom: '16px' }}>
            {selectedNode.description}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: '#f8fafc', padding: '16px', borderRadius: '8px' }}>
            <div>
              <strong style={{ fontSize: '0.85rem', color: '#475569' }}>Prerequisites in DAG:</strong>
              <div style={{ marginTop: '6px', fontSize: '0.85rem', color: '#0f172a' }}>
                {curriculumData?.edges
                  .filter((e) => e.to === selectedNode.id)
                  .map((e, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <ArrowRight size={14} color="#6366f1" />
                      <span>{e.prereq_name}</span>
                    </div>
                  )) || 'None (Foundational Entry Node)'}
              </div>
            </div>

            <div>
              <strong style={{ fontSize: '0.85rem', color: '#475569' }}>Dependent Downstream Concepts:</strong>
              <div style={{ marginTop: '6px', fontSize: '0.85rem', color: '#0f172a' }}>
                {curriculumData?.edges
                  .filter((e) => e.from === selectedNode.id)
                  .map((e, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                      <ArrowRight size={14} color="#059669" />
                      <span>{e.target_name}</span>
                    </div>
                  )) || 'Terminal Node (No further dependencies)'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
