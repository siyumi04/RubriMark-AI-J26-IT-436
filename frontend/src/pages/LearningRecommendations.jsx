import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import RecommendationCard from '../components/RecommendationCard';
import { BookOpenCheck, Filter, AlertCircle, CheckCircle } from 'lucide-react';

export default function LearningRecommendations({ activeStudent }) {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterPriority, setFilterPriority] = useState('ALL');

  useEffect(() => {
    if (activeStudent) {
      loadRecommendations();
    }
  }, [activeStudent]);

  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const data = await apiService.getStudentRecommendations(activeStudent.student_id);
      setRecommendations(data);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!activeStudent) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '50px' }}>
        <BookOpenCheck size={36} color="#6366f1" style={{ margin: '0 auto 12px auto' }} />
        <h3>No Student Selected</h3>
        <p style={{ color: '#64748b' }}>Please select a student to explore their customized learning recommendations.</p>
      </div>
    );
  }

  const filtered = recommendations.filter((r) => {
    if (filterPriority === 'ALL') return true;
    return r.priority_level?.toUpperCase() === filterPriority;
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Curated Learning Recommendations</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Verified study materials mapped directly to the detected knowledge gaps for <strong>{activeStudent.student_name}</strong>
          </p>
        </div>

        {/* Priority Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="#64748b" />
          <select
            className="form-control"
            style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
          >
            <option value="ALL">All Priorities</option>
            <option value="HIGH">High Priority</option>
            <option value="MEDIUM">Medium Priority</option>
            <option value="LOW">Low Priority</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading study recommendations...</div>
      ) : recommendations.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
          <CheckCircle size={36} color="#10b981" style={{ margin: '0 auto 8px auto' }} />
          <h3>All Core Learning Criteria Met</h3>
          <p style={{ color: '#64748b' }}>No remediation recommendations required for this student's submissions.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
          {filtered.map((rec) => (
            <RecommendationCard key={rec.id} recommendation={rec} />
          ))}
        </div>
      )}
    </div>
  );
}
