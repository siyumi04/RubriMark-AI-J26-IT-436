import React from 'react';
import { ExternalLink } from 'lucide-react';

export default function Header({ activeTab }) {
  const titles = {
    dashboard: {
      title: 'Academic Research Dashboard',
      subtitle: 'Adaptive AI-Based Rubric Generation & Criterion-Based Scoring Engine',
    },
    assessments: {
      title: 'Lecturer Assessment Creation',
      subtitle: 'Define subjective questions, reference criteria, and target cognitive levels',
    },
    analysis: {
      title: 'AI Question Analysis',
      subtitle: 'Cognitive complexity analysis, Bloom’s taxonomy mapping & entity extraction',
    },
    rubrics: {
      title: 'Adaptive Rubric Generation',
      subtitle: 'AI-synthesized multi-level descriptive rubrics calibrated to assessments',
    },
    weights: {
      title: 'Dynamic Weight Optimization',
      subtitle: 'Algorithmic weight balancing ensuring 100% mathematical normalization',
    },
    validation: {
      title: 'Automated Rubric Validation',
      subtitle: 'Coherence analysis, criterion completeness, and coverage verification',
    },
    approval: {
      title: 'Lecturer Rubric Editing & Approval',
      subtitle: 'Lecturer human-in-the-loop review, descriptor calibration, and official sign-off',
    },
    scoring: {
      title: 'Criterion-Based Student Scoring',
      subtitle: 'Granular AI evaluation against approved rubrics with formative feedback',
    },
    results: {
      title: 'Assessment Results & Cohort Analytics',
      subtitle: 'Holistic performance distributions, criterion heatmaps, and pass metrics',
    },
    dataset: {
      title: 'Dataset Integration & Research Evaluation',
      subtitle: 'Benchmark dataset analytics, provenance verification, and comparative metrics',
    },
  };

  const current = titles[activeTab] || titles.dashboard;

  return (
    <header className="top-header">
      <div className="header-title-block">
        <h2>{current.title}</h2>
        <p>{current.subtitle}</p>
      </div>

      <div className="header-actions">
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="btn btn-secondary btn-sm"
        >
          <ExternalLink size={14} />
          <span>FastAPI Docs</span>
        </a>

        <div className="user-profile-badge">
          <div className="avatar-circle">IT</div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.8rem' }}>Researcher</div>
            <div style={{ fontSize: '0.7rem', color: '#64748B' }}>IT23376472</div>
          </div>
        </div>
      </div>
    </header>
  );
}
