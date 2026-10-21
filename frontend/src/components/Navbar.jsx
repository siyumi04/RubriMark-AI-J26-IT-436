import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { Activity, Cpu, UserCheck } from 'lucide-react';

export default function Navbar({ activeStudent, onSelectStudentClick }) {
  const [health, setHealth] = useState({
    status: 'checking',
    model_loaded: false,
    model_status: 'Connecting...',
  });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiService.getHealth();
        setHealth(data);
      } catch (err) {
        setHealth({
          status: 'offline',
          model_loaded: false,
          model_status: 'Backend connection unavailable',
        });
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="top-navbar">
      <div className="navbar-left">
        <h1 className="page-title">Automated Short-Answer Assessment</h1>
      </div>

      <div className="navbar-right">
        {/* Active Student Badge */}
        {activeStudent ? (
          <div
            className="status-badge"
            style={{ backgroundColor: '#e0e7ff', color: '#3730a3', cursor: 'pointer' }}
            onClick={onSelectStudentClick}
            title="Click to change student"
          >
            <UserCheck size={14} />
            <span>Active: <strong>{activeStudent.student_name}</strong> ({activeStudent.student_id})</span>
          </div>
        ) : (
          <button
            className="btn btn-outline"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
            onClick={onSelectStudentClick}
          >
            <UserCheck size={14} /> Select Student
          </button>
        )}

        {/* Backend Status */}
        <div className={`status-badge ${health.status === 'healthy' ? 'online' : health.status === 'offline' ? 'offline' : 'warning'}`}>
          <span className="status-dot"></span>
          <span>FastAPI: {health.status}</span>
        </div>

        {/* AI Model Status */}
        <div
          className={`status-badge ${health.model_loaded ? 'online' : 'warning'}`}
          title={health.model_status}
        >
          <Cpu size={14} />
          <span>AI Model: {health.model_loaded ? 'Loaded' : 'Pending (.joblib)'}</span>
        </div>
      </div>
    </header>
  );
}
