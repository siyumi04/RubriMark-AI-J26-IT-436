import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { Users, Search, UserCheck, ArrowRight, Mail } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function StudentSelection({ activeStudent, onSelectStudent }) {
  const [students, setStudents] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadStudents();
  }, []);

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

  const filtered = students.filter(
    (s) =>
      s.student_name.toLowerCase().includes(search.toLowerCase()) ||
      s.student_id.toLowerCase().includes(search.toLowerCase()) ||
      (s.email && s.email.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Student Selection & Roster</h2>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Browse registered students, review submission volume, and activate candidates for feedback synthesis.
          </p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ position: 'relative' }}>
          <Search size={18} style={{ position: 'absolute', left: '14px', top: '14px', color: '#94a3b8' }} />
          <input
            type="text"
            className="form-control"
            style={{ paddingLeft: '42px', fontSize: '1rem' }}
            placeholder="Search students by registration ID, full name, or university email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>Loading student records...</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          No students found matching your query.
        </div>
      ) : (
        <div className="table-container card" style={{ padding: 0 }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Full Name</th>
                <th>Email Address</th>
                <th>Submissions</th>
                <th>Active Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => {
                const isActive = activeStudent?.student_id === s.student_id;
                return (
                  <tr key={s.student_id} style={{ backgroundColor: isActive ? '#f5f3ff' : undefined }}>
                    <td style={{ fontWeight: 600, color: '#4f46e5' }}>{s.student_id}</td>
                    <td style={{ fontWeight: 600 }}>{s.student_name}</td>
                    <td style={{ color: '#64748b' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                        <Mail size={14} color="#94a3b8" />
                        {s.email || 'N/A'}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-purple">
                        {s.answers_count || 0} Submissions
                      </span>
                    </td>
                    <td>
                      {isActive ? (
                        <span className="badge badge-emerald">
                          <UserCheck size={12} style={{ marginRight: '4px' }} /> Active Selection
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Inactive</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <button
                          className={`btn ${isActive ? 'btn-primary' : 'btn-outline'}`}
                          style={{ padding: '6px 12px', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                          title="Select student and view their dynamic AI dashboard"
                          onClick={() => {
                            onSelectStudent(s);
                            navigate('/');
                          }}
                        >
                          <span>{isActive ? 'View Dashboard' : 'Select & View Dashboard'}</span>
                          <ArrowRight size={14} />
                        </button>
                        <button
                          className="btn btn-outline"
                          style={{ padding: '6px 10px', fontSize: '0.8rem', color: '#64748b' }}
                          title="View answer analysis"
                          onClick={() => {
                            onSelectStudent(s);
                            navigate('/analysis');
                          }}
                        >
                          Analysis
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
