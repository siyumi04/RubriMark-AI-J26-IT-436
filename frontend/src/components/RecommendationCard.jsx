import React from 'react';
import { ExternalLink, BookOpen, Video, FileText, Code, Hash, Info } from 'lucide-react';

// API Base URL (leave empty to use relative URLs through Vite dev proxy, or override with VITE_API_BASE_URL)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export default function RecommendationCard({ recommendation }) {
  const {
    concept_name,
    resource_title,
    resource_type,
    resource_url,
    priority_level,
    verified_page,
    reason,
    lecture_number,
    practice_activity,
  } = recommendation;

  const getPriorityBadgeClass = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'badge-rose';
      case 'medium':
        return 'badge-amber';
      default:
        return 'badge-indigo';
    }
  };

  const getResourceIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'video':
        return <Video size={16} color="#8b5cf6" />;
      case 'exercise':
        return <Code size={16} color="#06b6d4" />;
      case 'article':
        return <FileText size={16} color="#4f46e5" />;
      default:
        return <BookOpen size={16} color="#4f46e5" />;
    }
  };

  /**
   * Build the correct PDF URL.
   * Handles relative URLs, absolute URLs, spaces in filenames, and the #page=X fragment.
   */
  const buildPdfUrl = () => {
    if (!resource_url) return '#';

    // Separate base path/query and hash fragment (e.g. #page=8)
    const [pathAndQuery, hash] = resource_url.split('#');

    // Clean and URL-encode the path component to handle any unencoded spaces in filenames
    const cleanPath = encodeURI(decodeURI(pathAndQuery));

    // Support both direct proxy (/api/lectures/...) and absolute backend URL
    let fullUrl = cleanPath;
    if (cleanPath.startsWith('http://') || cleanPath.startsWith('https://')) {
      fullUrl = cleanPath;
    } else if (API_BASE_URL) {
      const base = API_BASE_URL.replace(/\/$/, '');
      const path = cleanPath.startsWith('/') ? cleanPath : `/${cleanPath}`;
      fullUrl = `${base}${path}`;
    } else {
      fullUrl = cleanPath;
    }

    // Determine target page: hash from resource_url, or verified_page prop
    const targetPage = hash ? hash : (verified_page ? `page=${verified_page}` : '');

    return targetPage ? `${fullUrl}#${targetPage}` : fullUrl;
  };

  const pdfUrl = buildPdfUrl();

  return (
    <div
      className="card"
      style={{
        padding: '18px 20px',
        borderLeft:
          priority_level?.toLowerCase() === 'high'
            ? '4px solid #f43f5e'
            : priority_level?.toLowerCase() === 'medium'
            ? '4px solid #f59e0b'
            : '4px solid #6366f1',
      }}
    >
      {/* Header row: type + priority badge */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {getResourceIcon(resource_type)}
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            {resource_type || 'Academic Resource'}
          </span>
        </div>
        <span className={`badge ${getPriorityBadgeClass(priority_level)}`}>
          {priority_level || 'Medium'} Priority
        </span>
      </div>

      {/* Lecture Number */}
      {lecture_number && (
        <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '4px', fontWeight: 600 }}>
          {lecture_number}
        </div>
      )}

      {/* Title */}
      <h4 style={{ fontSize: '1rem', fontWeight: 600, color: '#0f172a', marginBottom: '6px' }}>
        {resource_title}
      </h4>

      {/* Concept badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Target Concept:</span>
        <span className="badge badge-purple" style={{ fontSize: '0.75rem' }}>
          {concept_name}
        </span>
      </div>

      {/* Verified page */}
      {verified_page && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <Hash size={13} color="#6366f1" />
          <span style={{ fontSize: '0.8rem', color: '#4f46e5', fontWeight: 600 }}>
            Verified Slide / Page {verified_page}
          </span>
        </div>
      )}

      {/* Reason */}
      {reason && (
        <div
          style={{
            fontSize: '0.78rem',
            color: '#64748b',
            lineHeight: 1.5,
            marginBottom: '10px',
            padding: '8px',
            backgroundColor: '#f8fafc',
            borderRadius: '6px',
            display: 'flex',
            gap: '6px',
          }}
        >
          <Info size={13} color="#94a3b8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{reason}</span>
        </div>
      )}

      {/* Practice activity */}
      {practice_activity && (
        <div
          style={{
            fontSize: '0.77rem',
            color: '#059669',
            lineHeight: 1.4,
            marginBottom: '12px',
            fontStyle: 'italic',
          }}
        >
          📝 {practice_activity}
        </div>
      )}

      {/* Access Study Material link opening in new tab */}
      <a
        href={pdfUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="btn btn-outline"
        style={{
          width: '100%',
          justifyContent: 'center',
          fontSize: '0.82rem',
          padding: '8px 12px',
          cursor: 'pointer',
          textDecoration: 'none',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          boxSizing: 'border-box',
        }}
        title={`Open ${resource_title || 'lecture PDF'} at page ${verified_page || 1}`}
      >
        <BookOpen size={14} />
        <span>Access Study Material</span>
        <ExternalLink size={14} />
      </a>
    </div>
  );
}
