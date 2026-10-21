import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import StudentSelector from './components/StudentSelector';
import Dashboard from './pages/Dashboard';
import StudentSelection from './pages/StudentSelection';
import AnswerAnalysis from './pages/AnswerAnalysis';
import KnowledgeGapDetection from './pages/KnowledgeGapDetection';
import ConceptDependencyAnalysis from './pages/ConceptDependencyAnalysis';
import PersonalizedFeedback from './pages/PersonalizedFeedback';
import LearningRecommendations from './pages/LearningRecommendations';
import FeedbackHistory from './pages/FeedbackHistory';
import { apiService } from './services/api';

const STORAGE_KEY = 'rubrimark_active_student';

/**
 * App – single source of truth for activeStudent.
 *
 * The selected student is persisted in localStorage so navigating between
 * pages and refreshing the browser does NOT lose the selection.
 * Every page receives the same activeStudent prop via the router, guaranteeing
 * a consistent student context across all views.
 */
export default function App() {
  const [activeStudent, setActiveStudentState] = useState(() => {
    // Restore previous session student from localStorage
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [isSelectorOpen, setIsSelectorOpen] = useState(false);

  // Wrapper that also persists to localStorage
  const setActiveStudent = (student) => {
    setActiveStudentState(student);
    try {
      if (student) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(student));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Ignore storage errors gracefully
    }
  };

  useEffect(() => {
    // If no student is stored, auto-select the first one from the API
    if (!activeStudent) {
      const fetchDefaultStudent = async () => {
        try {
          const students = await apiService.getStudents();
          if (students && students.length > 0) {
            setActiveStudent(students[0]);
          }
        } catch (err) {
          console.error('Failed to pre-load student roster:', err);
        }
      };
      fetchDefaultStudent();
    }
  }, []);

  return (
    <div className="app-container">
      {/* Dark Navy Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Navbar
          activeStudent={activeStudent}
          onSelectStudentClick={() => setIsSelectorOpen(true)}
        />

        <main className="content-area">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  activeStudent={activeStudent}
                  onSelectStudent={setActiveStudent}
                />
              }
            />
            <Route
              path="/students"
              element={
                <StudentSelection
                  activeStudent={activeStudent}
                  onSelectStudent={setActiveStudent}
                />
              }
            />
            <Route
              path="/analysis"
              element={<AnswerAnalysis activeStudent={activeStudent} />}
            />
            <Route
              path="/knowledge-gaps"
              element={<KnowledgeGapDetection activeStudent={activeStudent} />}
            />
            <Route
              path="/concept-dependencies"
              element={<ConceptDependencyAnalysis activeStudent={activeStudent} />}
            />
            <Route
              path="/feedback"
              element={<PersonalizedFeedback activeStudent={activeStudent} />}
            />
            <Route
              path="/recommendations"
              element={<LearningRecommendations activeStudent={activeStudent} />}
            />
            <Route
              path="/history"
              element={<FeedbackHistory activeStudent={activeStudent} />}
            />
          </Routes>
        </main>
      </div>

      {/* Quick Student Selector Modal */}
      <StudentSelector
        isOpen={isSelectorOpen}
        onClose={() => setIsSelectorOpen(false)}
        onSelectStudent={setActiveStudent}
        currentStudentId={activeStudent?.student_id}
      />
    </div>
  );
}
