import React, { createContext, useContext, useState, useEffect } from 'react';

const STORAGE_KEY = 'rubrimark_active_student';

const StudentContext = createContext(null);

/**
 * StudentProvider wraps the entire app and provides a single source of truth
 * for the currently selected student. The selection is persisted in localStorage
 * so page refreshes do not lose the active student.
 */
export function StudentProvider({ children }) {
  const [activeStudent, setActiveStudentState] = useState(() => {
    // Restore from localStorage on initial mount
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const setActiveStudent = (student) => {
    setActiveStudentState(student);
    try {
      if (student) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(student));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Ignore storage errors
    }
  };

  return (
    <StudentContext.Provider value={{ activeStudent, setActiveStudent }}>
      {children}
    </StudentContext.Provider>
  );
}

/**
 * Hook to consume the StudentContext. Throws if used outside a StudentProvider.
 */
export function useStudent() {
  const ctx = useContext(StudentContext);
  if (!ctx) {
    throw new Error('useStudent must be used within a StudentProvider');
  }
  return ctx;
}
