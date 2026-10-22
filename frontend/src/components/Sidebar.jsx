import React from 'react';
import {
  LayoutDashboard,
  FilePlus,
  Cpu,
  Layers,
  Sliders,
  CheckCircle2,
  Edit3,
  GraduationCap,
  BarChart3,
  Sparkles,
  Database,
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, systemHealth }) {
  const navItems = [
    { id: 'dashboard', label: 'Research Overview', icon: LayoutDashboard },
    { id: 'assessments', label: '1. Assessment Creation', icon: FilePlus, step: '1' },
    { id: 'analysis', label: '2. AI Question Analysis', icon: Cpu, step: '2' },
    { id: 'rubrics', label: '3. Adaptive Rubrics', icon: Layers, step: '3' },
    { id: 'weights', label: '4. Dynamic Weights', icon: Sliders, step: '4' },
    { id: 'validation', label: '5. Rubric Validation', icon: CheckCircle2, step: '5' },
    { id: 'approval', label: '6. Editing & Approval', icon: Edit3, step: '6' },
    { id: 'scoring', label: '7. Student Scoring', icon: GraduationCap, step: '7' },
    { id: 'results', label: '8. Assessment Results', icon: BarChart3, step: '8' },
    { id: 'dataset', label: '9. Dataset & Research Evaluation', icon: Database, step: '9' },
  ];


  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-row">
          <div className="logo-badge">R</div>
          <div className="logo-text">
            <h1>RubriMark AI</h1>
            <span>Research System</span>
          </div>
        </div>

        <div className="research-chip">
          <strong>Component: IT23376472</strong>
          <div>Adaptive Rubric Generation & Criterion Scoring</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">Core Navigation</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              {item.step ? (
                <span className="nav-step-number">{item.step}</span>
              ) : (
                <Icon size={18} className="nav-icon" />
              )}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="system-status-indicator">
          <span
            className="status-dot"
            style={{
              backgroundColor: systemHealth?.status === 'healthy' ? '#10B981' : '#EF4444',
            }}
          />
          <span>Backend: {systemHealth?.status === 'healthy' ? 'Online' : 'Connecting...'}</span>
        </div>
        <Sparkles size={14} color="#818CF8" />
      </div>
    </aside>
  );
}
