import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function PerformanceChart({ answers = [] }) {
  if (!answers || answers.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
        No assessment records available for performance analytics.
      </div>
    );
  }

  const chartData = answers.map((ans) => ({
    name: ans.question_id,
    obtained: ans.obtained_marks !== null && ans.obtained_marks !== undefined ? ans.obtained_marks : 0,
    total: ans.question?.total_marks || 10.0,
    subject: ans.question?.subject || 'CS',
  }));

  return (
    <div style={{ width: '100%', height: 280 }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 20, left: -10, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
          <YAxis domain={[0, 10]} tick={{ fill: '#64748b', fontSize: 12 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="obtained" name="Obtained Marks" fill="#6366f1" radius={[4, 4, 0, 0]} />
          <Bar dataKey="total" name="Available Total" fill="#e2e8f0" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
