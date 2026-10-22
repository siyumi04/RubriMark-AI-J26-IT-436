const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const api = {
  // System Health
  async getHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (!res.ok) throw new Error('Healthcheck failed');
      return await res.json();
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  },

  // 1. Assessments
  async getAssessments() {
    const res = await fetch(`${API_BASE}/assessments/`);
    if (!res.ok) throw new Error('Failed to fetch assessments');
    return await res.json();
  },

  async createAssessment(data) {
    const res = await fetch(`${API_BASE}/assessments/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create assessment');
    return await res.json();
  },

  // 2. AI Question Analysis
  async analyzeQuestion(questionText, referenceAnswer = null) {
    const res = await fetch(`${API_BASE}/analysis/question`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_text: questionText, reference_answer: referenceAnswer }),
    });
    if (!res.ok) throw new Error('Failed to analyze question');
    return await res.json();
  },

  // 3. Adaptive Rubric Generation (Rule-Based Baseline)
  async generateRubric(input) {
    const payload = typeof input === 'object' ? input : { assessment_id: input };
    const res = await fetch(`${API_BASE}/rubrics/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to generate rubric' }));
      throw new Error(err.detail || 'Failed to generate rubric');
    }
    return await res.json();
  },

  async getRubricsForAssessment(assessmentId) {
    const res = await fetch(`${API_BASE}/rubrics/assessment/${assessmentId}`);
    if (!res.ok) throw new Error('Failed to fetch rubrics');
    return await res.json();
  },

  // 4. Dynamic Weight Optimization
  async optimizeWeights(rubricId) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/optimize-weights`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to optimize weights');
    return await res.json();
  },

  // 5. Rubric Validation
  async validateRubric(rubricId) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/validate`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to validate rubric');
    return await res.json();
  },

  // 6. Lecturer Rubric Approval
  async approveRubric(rubricId, approvedBy = 'Dr. Lecturer', notes = 'Approved') {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved_by: approvedBy, notes: notes }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to approve rubric' }));
      throw new Error(err.detail || 'Failed to approve rubric');
    }
    return await res.json();
  },

  // Phase 3: Lecturer Rejection
  async rejectRubric(rubricId, data) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rejection_reasons: data.rejection_reasons || [],
        feedback: data.feedback || null,
        rejected_by: data.rejected_by || 'Dr. Lecturer',
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to reject rubric' }));
      throw new Error(err.detail || 'Failed to reject rubric');
    }
    return await res.json();
  },

  // Phase 3: Feedback-Driven Rubric Regeneration
  async regenerateRubric(rubricId, data = {}) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rejection_reasons: data.rejection_reasons || null,
        feedback: data.feedback !== undefined ? data.feedback : null,
        rejected_by: data.rejected_by || 'Dr. Lecturer',
        use_rag: data.use_rag !== undefined ? data.use_rag : true,
        force_fallback: data.force_fallback || false,
        generation_mode: data.generation_mode || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to regenerate rubric' }));
      throw new Error(err.detail || 'Failed to regenerate rubric');
    }
    return await res.json();
  },

  // Phase 3: Rubric Version History
  async getRubricHistory(rubricId) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}/history`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch rubric history' }));
      throw new Error(err.detail || 'Failed to fetch rubric history');
    }
    return await res.json();
  },

  async getAssessmentRubricHistory(assessmentId) {
    const res = await fetch(`${API_BASE}/rubrics/assessment/${assessmentId}/history`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch assessment rubric history' }));
      throw new Error(err.detail || 'Failed to fetch assessment rubric history');
    }
    return await res.json();
  },

  async getRubricDetail(rubricId) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to fetch rubric detail' }));
      throw new Error(err.detail || 'Failed to fetch rubric detail');
    }
    return await res.json();
  },

  // 7. Student Answer Scoring
  async evaluateStudentAnswer(data) {
    const res = await fetch(`${API_BASE}/scoring/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to evaluate answer');
    return await res.json();
  },

  async getSubmissions(assessmentId) {
    const res = await fetch(`${API_BASE}/scoring/assessment/${assessmentId}`);
    if (!res.ok) throw new Error('Failed to fetch submissions');
    return await res.json();
  },

  // Rubric Editing
  async updateRubric(rubricId, data) {
    const res = await fetch(`${API_BASE}/rubrics/${rubricId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update rubric');
    return await res.json();
  },

  // 8. Assessment Results & Analytics
  async getAssessmentResults(assessmentId) {
    const res = await fetch(`${API_BASE}/results/assessment/${assessmentId}`);
    if (!res.ok) throw new Error('Failed to fetch assessment results');
    return await res.json();
  },

  // 9. Dataset Integration & Research Evaluation
  async getDatasetStatus(scope = 'benchmark') {
    const res = await fetch(`${API_BASE}/dataset/status?scope=${encodeURIComponent(scope)}`);
    if (!res.ok) throw new Error('Failed to fetch dataset status');
    return await res.json();
  },

  async importLecturerRubric(file = null) {
    let res;
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      res = await fetch(`${API_BASE}/dataset/import-lecturer-rubric`, {
        method: 'POST',
        body: formData,
      });
    } else {
      res = await fetch(`${API_BASE}/dataset/import-lecturer-rubric`, {
        method: 'POST',
      });
    }
    if (!res.ok) throw new Error('Failed to import lecturer rubric');
    return await res.json();
  },

  async importStudentResponses(file = null) {
    let res;
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      res = await fetch(`${API_BASE}/dataset/import-student-responses`, {
        method: 'POST',
        body: formData,
      });
    } else {
      res = await fetch(`${API_BASE}/dataset/import-student-responses`, {
        method: 'POST',
      });
    }
    if (!res.ok) throw new Error('Failed to import student responses');
    return await res.json();
  },

  async batchEvaluate(scoringMethod = 'semantic', assessmentId = null) {
    const res = await fetch(`${API_BASE}/dataset/batch-evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scoring_method: scoringMethod, assessment_id: assessmentId }),
    });
    if (!res.ok) throw new Error('Batch evaluation failed');
    return await res.json();
  },

  async getResearchMetrics(scope = 'benchmark') {
    const res = await fetch(`${API_BASE}/dataset/research-metrics?scope=${encodeURIComponent(scope)}`);
    if (!res.ok) throw new Error('Failed to fetch research metrics');
    return await res.json();
  },
};

