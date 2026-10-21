import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Search, UserCheck, X } from 'lucide-react';

export default function StudentSelector({ isOpen, onClose, onSelectStudent, currentStudentId }) {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadStudents();
    }
  }, [isOpen]);

  const loadStudents = async () => {
    setLoading(true);
    try {
      const data = await apiService.getStudents();
      setStudents(data);
    } catch (err) {
      console.error('Failed to load students:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const filtered = students.filter(
    (s) =>
      s.student_name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_id.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.6)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        backdropFilter: 'blur(3px)',
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{
          width: '500px',
          maxWidth: '90%',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#ffffff',
          borderRadius: '16px',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card-header" style={{ paddingBottom: '12px' }}>
          <h3 className="card-title">
            <UserCheck size={20} color="#4f46e5" /> Select Student for Feedback Analysis
          </h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ position: 'relative', marginBottom: '16px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: '#94a3b8' }} />
          <input
            type="text"
            className="form-control"
            style={{ paddingLeft: '36px' }}
            placeholder="Search by student ID or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            autoFocus
          />
        </div>

        <div style={{ flex: 1, overflowY: 'auto', maxHeight: '350px' }}>
          {loading ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>Loading students...</div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: '#64748b' }}>No students found matching your query.</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {filtered.map((s) => {
                const isSelected = currentStudentId === s.student_id;
                return (
                  <div
                    key={s.student_id}
                    onClick={() => {
                      onSelectStudent(s);
                      onClose();
                    }}
                    style={{
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: isSelected ? '2px solid #4f46e5' : '1px solid #e2e8f0',
                      backgroundColor: isSelected ? '#f5f3ff' : '#ffffff',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>{s.student_name}</div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        ID: {s.student_id} | {s.email || 'No email registered'}
                      </div>
                    </div>
                    <span className="badge badge-indigo">
                      {s.answers_count || 0} Answers
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
