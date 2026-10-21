import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  BrainCircuit,
  MessageSquareText,
  BookOpenCheck,
  History,
  FileCheck2,
  Sparkles,
  GitMerge,
} from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/students', label: 'Student Selection', icon: Users },
    { to: '/analysis', label: 'Answer Analysis', icon: FileCheck2 },
    { to: '/knowledge-gaps', label: 'Knowledge Gap Detection', icon: BrainCircuit },
    { to: '/concept-dependencies', label: 'Concept Dependency Analysis', icon: GitMerge },
    { to: '/feedback', label: 'Personalized Feedback', icon: MessageSquareText },
    { to: '/recommendations', label: 'Learning Recommendations', icon: BookOpenCheck },
    { to: '/history', label: 'Feedback History', icon: History },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon">
          <Sparkles size={22} />
        </div>
        <div className="brand-text">
          <h2>RubriMark AI</h2>
          <p>Explainable Feedback Hub</p>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section-title">Academic Assessment</div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end={item.to === '/'}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div><strong>RubriMark AI Framework</strong></div>
        <div style={{ marginTop: '4px', opacity: 0.8 }}>Explainable Assessment Engine</div>
      </div>
    </aside>
  );
}
