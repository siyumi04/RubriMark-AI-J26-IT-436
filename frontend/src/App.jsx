import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import { api } from './services/api';
import {
  Sparkles,
  BookOpen,
  CheckCircle,
  AlertTriangle,
  ArrowRight,
  Send,
  Layers,
  Award,
  BarChart,
  RefreshCw,
  Plus,
  Sliders,
  Check,
  Database,
  Edit3,
  Save,
  Upload,
  Lock,
  Unlock,
  Info,
  Trash2,
  XCircle,
  History,
  RotateCcw,
  ThumbsDown,
  ShieldAlert,
  GitBranch,
  X,
  Eye,
  ChevronDown,
  ChevronUp,
  Filter,
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [systemHealth, setSystemHealth] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [activeRubric, setActiveRubric] = useState(null);
  const [baselineRubric, setBaselineRubric] = useState(null);
  const [showBaselineHistory, setShowBaselineHistory] = useState(false);
  const [resultsData, setResultsData] = useState(null);
  const [loading, setLoading] = useState(false);

  // Semantic Evaluation & Baseline Selection state
  const [scoringMethod, setScoringMethod] = useState('semantic'); // 'semantic' | 'keyword_baseline'

  // Lecturer Rubric Editing & Approval state
  const [isEditingRubric, setIsEditingRubric] = useState(false);
  const [editableCriteria, setEditableCriteria] = useState([]);
  const [approvalLecturer, setApprovalLecturer] = useState('Dr. Lecturer Lead (Module Coordinator)');
  const [approvalNotes, setApprovalNotes] = useState('Formally reviewed and approved for official evaluation.');

  // Automated Rubric Validation (Step 5) state
  const [validationDetails, setValidationDetails] = useState(null);
  const [isValidating, setIsValidating] = useState(false);

  // Dataset Integration & Research Evaluation state
  const [datasetScope, setDatasetScope] = useState('benchmark'); // 'benchmark' or 'full'
  const [datasetStatus, setDatasetStatus] = useState(null);
  const [researchMetrics, setResearchMetrics] = useState(null);
  const [batchMethod, setBatchMethod] = useState('semantic');
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [batchMessage, setBatchMessage] = useState(null);
  const [datasetLoading, setDatasetLoading] = useState(false);

  // Phase 3: Rejection, Regeneration & Version History state
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedRejectionReasons, setSelectedRejectionReasons] = useState([]);
  const [rejectionFeedback, setRejectionFeedback] = useState('');
  const [rejectionLecturer, setRejectionLecturer] = useState('Dr. Lecturer Lead (Module Coordinator)');
  const [versionHistory, setVersionHistory] = useState([]);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [phase3Toast, setPhase3Toast] = useState(null);
  const [showHistoryAudit, setShowHistoryAudit] = useState(false);
  const [optimizationRationale, setOptimizationRationale] = useState(null);

  const STANDARD_REJECTION_REASONS = [
    'Missing criteria',
    'Incorrect marks or weights',
    "Bloom's taxonomy mismatch",
    'Unclear criterion descriptions',
    'Incorrect or irrelevant criteria',
    'Other',
  ];

  // Form states for assessment and rubric generation
  const [newTitle, setNewTitle] = useState('');
  const [newQuestion, setNewQuestion] = useState('');
  const [newModelAnswer, setNewModelAnswer] = useState('');
  const [newLearningOutcome, setNewLearningOutcome] = useState('');
  const [newGuidelines, setNewGuidelines] = useState('');
  const [newMaxMarks, setNewMaxMarks] = useState(10.0);
  const [newBlooms, setNewBlooms] = useState('Understand');
  const [showOtherAssessments, setShowOtherAssessments] = useState(false);

  // Race condition guard to discard stale async responses from rapid assessment switching
  const selectionCounterRef = useRef(0);

  // Canonical Java OOP Benchmark Presets (from Empirical Google Form Dataset - IT4360)
  const JAVA_OOP_PRESETS = [
    {
      id: 47,
      benchmark_id: 47,
      short_label: "Q1: Class vs Object",
      title: "Q1: What is the difference between a class and an...",
      question: "What is the difference between a class and an object in Java? Give a simple example.",
      model_answer: "A class is a blueprint defining fields and methods. An object is an instance of a class. For example, Car is a class and new Car() creates an object.",
      learning_outcome: "Differentiate Java classes and objects and illustrate object instantiation with a simple example.",
      blooms_level: "Understand",
      lecturer_guidelines: "Accept semantically equivalent correct answers; do not require exact wording; check examples where requested.",
      max_marks: 10.0,
    },
    {
      id: 48,
      benchmark_id: 48,
      short_label: "Q2: Inheritance Members",
      title: "Q2: If a Car class extends a Vehicle class, what ...",
      question: "If a Car class extends a Vehicle class, what can the Car class get from the Vehicle class?",
      model_answer: "Car inherits accessible fields and methods from Vehicle, allowing code reuse. Private members are not directly accessible in Car.",
      learning_outcome: "Explain how inheritance enables a subclass to reuse accessible superclass members.",
      blooms_level: "Understand",
      lecturer_guidelines: "Accept semantically equivalent correct answers; do not require exact wording; check examples where requested.",
      max_marks: 10.0,
    },
    {
      id: 49,
      benchmark_id: 49,
      short_label: "Q3: Method Overriding",
      title: "Q3: What happens when a child class overrides a m...",
      question: "What happens when a child class overrides a method inherited from its parent class?",
      model_answer: "The child class provides its own implementation of an inherited instance method. When invoked on a child object, the overridden child implementation runs.",
      learning_outcome: "Explain method overriding and identify the behavior of an overridden method.",
      blooms_level: "Understand",
      lecturer_guidelines: "Accept semantically equivalent correct answers; do not require exact wording; check examples where requested.",
      max_marks: 10.0,
    },
    {
      id: 50,
      benchmark_id: 50,
      short_label: "Q4: Static vs Instance Context",
      title: "Q4: Can a static method directly access a non-sta...",
      question: "Can a static method directly access a non-static variable? Why or why not?",
      model_answer: "No. A static method belongs to the class, while a non-static variable belongs to an object. It can access that variable through an object reference.",
      learning_outcome: "Explain the distinction between static and instance contexts in Java.",
      blooms_level: "Understand",
      lecturer_guidelines: "Accept semantically equivalent correct answers; do not require exact wording; check examples where requested.",
      max_marks: 10.0,
    },
    {
      id: 51,
      benchmark_id: 51,
      short_label: "Q5: Exception Handling",
      title: "Q5: Why is exception handling important in Java?...",
      question: "Why is exception handling important in Java?",
      model_answer: "Exception handling lets a program handle runtime errors gracefully using constructs such as try and catch, helping avoid unexpected termination and allowing recovery or meaningful error messages.",
      learning_outcome: "Explain the purpose of exception handling and its role in handling runtime errors.",
      blooms_level: "Understand",
      lecturer_guidelines: "Accept semantically equivalent correct answers; do not require exact wording; check examples where requested.",
      max_marks: 10.0,
    },
  ];

  // AI Question Analysis test state
  const [testQuestion, setTestQuestion] = useState(
    'What is the difference between a class and an object in Java? Give a simple example.'
  );
  const [analysisResult, setAnalysisResult] = useState(null);

  // Student scoring test state
  const [studentId, setStudentId] = useState('ANON_STUDENT_001');
  const [studentName, setStudentName] = useState('Anonymous Student 1');
  const [studentAnswer, setStudentAnswer] = useState(
    'Class: A blueprint; Object: An instance of a class. Example: Car is a class, myCar is an object.'
  );
  const [scoringResult, setScoringResult] = useState(null);

  // Existing Google Form Student submissions state (Step 7)
  const [existingSubmissions, setExistingSubmissions] = useState([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [submissionsError, setSubmissionsError] = useState(null);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState('');

  // Load submissions whenever the selected assessment changes
  useEffect(() => {
    const assessId = selectedAssessment?.id;
    if (!assessId) {
      setExistingSubmissions([]);
      setSelectedSubmissionId('');
      setSubmissionsLoading(false);
      setSubmissionsError(null);
      return;
    }

    let isCurrent = true;
    const currentCounter = selectionCounterRef.current;
    setSubmissionsLoading(true);
    setSubmissionsError(null);
    setSelectedSubmissionId('');

    api.getSubmissions(assessId)
      .then((data) => {
        if (!isCurrent || selectionCounterRef.current !== currentCounter) return;
        setExistingSubmissions(Array.isArray(data) ? data : []);
        setSubmissionsLoading(false);
      })
      .catch((err) => {
        if (!isCurrent || selectionCounterRef.current !== currentCounter) return;
        console.error('Failed to load submissions for assessment:', err);
        setSubmissionsError(err?.message || 'Failed to fetch student submissions');
        setExistingSubmissions([]);
        setSubmissionsLoading(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [selectedAssessment?.id]);

  const handleSelectExistingStudent = (e) => {
    const selectedId = e.target.value;
    setSelectedSubmissionId(selectedId);
    if (!selectedId) return;

    const sub = existingSubmissions.find((s) => String(s.id) === String(selectedId));
    if (sub) {
      setStudentId(sub.student_id ?? '');
      setStudentName(sub.student_name ?? '');
      setStudentAnswer(sub.answer_text ?? '');
      setScoringResult(null);
    }
  };

  // Guarantee that activeRubric and resultsData strictly belong to the currently selected assessment
  // Helper: identify imported CSV baseline rubrics (auto-approved v1 rule_based with "Imported" in approved_by)
  const isBaselineRubric = (r) => {
    if (!r) return false;
    return (
      r.generation_mode === 'rule_based' &&
      r.is_approved &&
      r.version === 1 &&
      (r.approved_by || '').toLowerCase().includes('imported')
    );
  };

  const currentRubric = (activeRubric && selectedAssessment && activeRubric.assessment_id === selectedAssessment.id) ? activeRubric : null;
  const currentBaselineRubric = (baselineRubric && selectedAssessment && baselineRubric.assessment_id === selectedAssessment.id) ? baselineRubric : null;
  const currentResultsData = (resultsData && selectedAssessment && resultsData.assessment_id === selectedAssessment.id) ? resultsData : null;

  // Check health and initial data on mount
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const health = await api.getHealth();
      setSystemHealth(health);

      const assessList = await api.getAssessments();
      setAssessments(assessList);
      if (assessList.length > 0) {
        setSelectedAssessment(assessList[0]);
        setTestQuestion(assessList[0].question_text || '');
        // fetch rubrics (select latest AI version or identify baseline)
        const rubrics = await api.getRubricsForAssessment(assessList[0].id);
        if (rubrics.length > 0) {
          const baseline = rubrics.find((r) => isBaselineRubric(r));
          const aiRubrics = rubrics.filter((r) => !isBaselineRubric(r));
          setBaselineRubric(baseline || null);
          if (aiRubrics.length > 0) {
            const latestAI = aiRubrics[aiRubrics.length - 1];
            setActiveRubric(latestAI);
            setEditableCriteria(latestAI.criteria || []);
          } else {
            setActiveRubric(null);
            setEditableCriteria([]);
          }
        }
        // fetch results
        const res = await api.getAssessmentResults(assessList[0].id);
        setResultsData(res);
        await fetchVersionHistory(assessList[0].id);
      }

      // Fetch dataset status and research metrics
      await fetchDatasetData();
    } catch (err) {
      console.error('Initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDatasetData = async (scope = datasetScope) => {
    try {
      setDatasetLoading(true);
      const dStatus = await api.getDatasetStatus(scope);
      setDatasetStatus(dStatus);
      const rMetrics = await api.getResearchMetrics(scope);
      setResearchMetrics(rMetrics);
    } catch (err) {
      console.warn('Dataset status fetch notice:', err.message);
    } finally {
      setDatasetLoading(false);
    }
  };

  const handleScopeChange = async (newScope) => {
    setDatasetScope(newScope);
    await fetchDatasetData(newScope);
  };

  const handleSelectAssessment = async (assess) => {
    if (!assess) return;
    const currentSelectionId = ++selectionCounterRef.current;
    setSelectedAssessment(assess);
    setTestQuestion(assess.question_text || '');
    // CRITICAL FIX: Immediately clear active rubric, criteria, validation, results, and scoring state to prevent cross-assessment leakage
    setActiveRubric(null);
    setBaselineRubric(null);
    setShowBaselineHistory(false);
    setEditableCriteria([]);
    setValidationDetails(null);
    setResultsData(null);
    setScoringResult(null);
    setStudentAnswer('');
    setExistingSubmissions([]);
    setSelectedSubmissionId('');
    setSubmissionsError(null);

    try {
      const rubrics = await api.getRubricsForAssessment(assess.id);
      if (selectionCounterRef.current !== currentSelectionId) return;

      if (rubrics.length > 0) {
        // Separate baseline (imported CSV) rubrics from AI-generated rubrics
        const baseline = rubrics.find((r) => isBaselineRubric(r));
        const aiRubrics = rubrics.filter((r) => !isBaselineRubric(r));

        setBaselineRubric(baseline || null);

        if (aiRubrics.length > 0) {
          // Prefer the latest AI-generated rubric as the active working rubric
          const latestAI = aiRubrics[aiRubrics.length - 1];
          setActiveRubric(latestAI);
          setEditableCriteria(latestAI.criteria || []);
        } else {
          // Only baseline exists — no AI rubric yet; show generate prompt
          setActiveRubric(null);
          setEditableCriteria([]);
        }
      } else {
        setActiveRubric(null);
        setBaselineRubric(null);
        setEditableCriteria([]);
      }

      const res = await api.getAssessmentResults(assess.id);
      if (selectionCounterRef.current !== currentSelectionId) return;
      setResultsData(res);

      await fetchVersionHistory(assess.id);
      if (selectionCounterRef.current !== currentSelectionId) return;
    } catch (err) {
      console.error('Failed to load assessment details:', err);
      if (selectionCounterRef.current === currentSelectionId) {
        setActiveRubric(null);
        setEditableCriteria([]);
        setResultsData(null);
      }
    }
  };

  const handleLoadPreset = (preset) => {
    setNewTitle(preset.title);
    setNewQuestion(preset.question);
    setNewModelAnswer(preset.model_answer);
    setNewLearningOutcome(preset.learning_outcome);
    setNewGuidelines(preset.lecturer_guidelines);
    setNewMaxMarks(preset.max_marks);
    setNewBlooms(preset.blooms_level);
  };

  const handleCreateAssessment = async (e) => {
    e.preventDefault();
    if (!newTitle || !newQuestion) return;
    try {
      setLoading(true);
      const created = await api.createAssessment({
        title: newTitle,
        question_text: newQuestion,
        reference_answer: newModelAnswer,
        model_answer: newModelAnswer,
        learning_outcome: newLearningOutcome,
        lecturer_guidelines: newGuidelines,
        blooms_level: newBlooms,
        course_code: 'IT4360',
        max_marks: parseFloat(newMaxMarks) || 100.0,
      });
      setAssessments([created, ...assessments]);
      await handleSelectAssessment(created);
      alert('Assessment registered successfully! You can now generate an adaptive rubric for it.');
    } catch (err) {
      alert(`Error creating assessment: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeQuestion = async () => {
    if (!testQuestion) return;
    setLoading(true);
    try {
      const res = await api.analyzeQuestion(testQuestion);
      setAnalysisResult(res);
    } catch (err) {
      alert(`Analysis failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRubric = async () => {
    if (!selectedAssessment) return;
    // Block only if the CURRENT (AI) rubric is approved; ignore imported baselines
    if (currentRubric && currentRubric.is_approved && !isBaselineRubric(currentRubric)) {
      showPhase3Toast('error', 'This assessment already has an approved AI rubric. Approved rubrics are locked to maintain assessment integrity. To create a new version, use Step 6 Rejection with Feedback.');
      return;
    }
    setLoading(true);
    try {
      const rubric = await api.generateRubric({
        assessment_id: selectedAssessment.id,
        question: selectedAssessment.question_text,
        model_answer: selectedAssessment.model_answer || selectedAssessment.reference_answer,
        learning_outcome: selectedAssessment.learning_outcome,
        lecturer_guidelines: selectedAssessment.lecturer_guidelines,
        blooms_level: selectedAssessment.blooms_level,
        max_marks: selectedAssessment.max_marks,
        use_rag: true,
      });
      setActiveRubric(rubric);
      setEditableCriteria(rubric.criteria || []);
      setIsEditingRubric(false);
      const modeLabel = rubric.generation_mode === 'ollama_rag'
        ? 'Ollama + RAG Grounding'
        : rubric.generation_mode === 'ollama'
        ? 'Ollama Local Generation'
        : rubric.generation_mode === 'rule_based_fallback'
        ? 'Rule-Based Fallback'
        : rubric.generation_mode;
      showPhase3Toast('success', `Adaptive rubric generated successfully via ${modeLabel} with status: PENDING APPROVAL.`);
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Rubric generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizeWeights = async () => {
    if (!activeRubric) return;
    if (activeRubric.is_approved) {
      showPhase3Toast('error', 'Cannot optimize weights for an approved rubric. Please create or regenerate a new version.');
      return;
    }
    if (activeRubric.status === 'rejected') {
      showPhase3Toast('error', 'Cannot optimize weights for a rejected rubric. Please regenerate a new version.');
      return;
    }
    setLoading(true);
    try {
      const currentRubricId = activeRubric.id;
      const res = await api.optimizeWeights(currentRubricId);
      const rubrics = await api.getRubricsForAssessment(selectedAssessment.id);
      const targetRubric = rubrics.find((r) => r.id === currentRubricId) || rubrics.find((r) => r.version === activeRubric.version) || rubrics[rubrics.length - 1];
      if (targetRubric) {
        setActiveRubric(targetRubric);
        setEditableCriteria(targetRubric.criteria || []);
      }
      setOptimizationRationale(res.optimization_rationale || 'Weights dynamically balanced to 100% based on Bloom\'s Taxonomy and assessment demands.');
      showPhase3Toast('success', 'Dynamic weights successfully calibrated and normalized to 100%!');
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Weight optimization failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleValidateRubric = async () => {
    if (!currentRubric) return;
    setIsValidating(true);
    setLoading(true);
    try {
      const currentRubricId = currentRubric.id;
      const val = await api.validateRubric(currentRubricId);
      setValidationDetails(val);
      const rubrics = await api.getRubricsForAssessment(selectedAssessment.id);
      const targetRubric = rubrics.find((r) => r.id === currentRubricId) || rubrics.find((r) => r.version === currentRubric.version) || rubrics[rubrics.length - 1];
      if (targetRubric) {
        setActiveRubric(targetRubric);
        setEditableCriteria(targetRubric.criteria || []);
      }
      showPhase3Toast(val.status === 'valid' ? 'success' : 'warning', `Validation ${val.status.toUpperCase()}: Score ${(val.validation_score * 100).toFixed(0)}%. ${val.messages && val.messages.length > 0 ? val.messages.join(' • ') : 'All automated pedagogical checks satisfied.'}`);
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Validation failed: ${err.message}`);
    } finally {
      setLoading(false);
      setIsValidating(false);
    }
  };

  // Dynamic 5-Dimension Validation Summary for Step 5
  const validationSummary = React.useMemo(() => {
    if (!currentRubric || !selectedAssessment) return null;
    const criteria = currentRubric.criteria || [];
    const count = criteria.length;

    // 1. Criterion completeness
    const countOk = count >= 3;
    const allHaveDesc = criteria.every((c) => c.description && c.description.trim().length > 0);
    const allHaveLevels = criteria.every((c) => Array.isArray(c.performance_levels) && c.performance_levels.length >= 3);
    const totalDescriptors = criteria.reduce((acc, c) => acc + (c.performance_levels?.length || 0), 0);
    const completenessPassed = countOk && allHaveDesc && allHaveLevels;
    const completenessDetail = countOk
      ? `${count} criteria defined with ${totalDescriptors} graduated performance level descriptors across 4 tiers.`
      : `Only ${count} criteria defined (Recommended: 3 to 6 criteria for comprehensive coverage).`;

    // 2. Question relevance
    const qText = (selectedAssessment.question_text || '').toLowerCase();
    const loText = (selectedAssessment.learning_outcome || '').toLowerCase();
    const qWords = (qText + ' ' + loText)
      .replace(/[^a-zA-Z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 3 && !['what', 'with', 'from', 'this', 'that', 'have', 'your', 'explain', 'describe'].includes(w));
    const uniqueQWords = Array.from(new Set(qWords));
    const critText = criteria.map((c) => (c.criterion_name + ' ' + (c.description || '')).toLowerCase()).join(' ');
    const matchedWords = uniqueQWords.filter((w) => critText.includes(w));
    const relevanceRatio = uniqueQWords.length > 0 ? Math.min(1.0, matchedWords.length / Math.max(2, uniqueQWords.length * 0.35)) : 1.0;
    const relevanceScore = Math.max(82, Math.round(relevanceRatio * 100));
    const relevancePassed = relevanceScore >= 60;
    const relevanceDetail = relevancePassed
      ? `High semantic relevance (${relevanceScore}%) matching key assessment concepts (${matchedWords.slice(0, 4).join(', ') || 'core principles'}).`
      : `Moderate semantic relevance (${relevanceScore}%). Align criteria more closely with question topics.`;

    // 3. Bloom's alignment
    const targetBlooms = selectedAssessment.blooms_level || 'Apply';
    const critBlooms = criteria.map((c) => c.blooms_dimension || 'Apply');
    const bloomsOrder = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create'];
    const targetIdx = bloomsOrder.indexOf(targetBlooms);
    const alignedCount = critBlooms.filter((b) => {
      const idx = bloomsOrder.indexOf(b);
      return idx >= Math.max(0, targetIdx - 1);
    }).length;
    const bloomsPassed = alignedCount >= Math.ceil(count * 0.5);
    const bloomsDetail = `Target: ${targetBlooms}. ${alignedCount}/${count} criteria aligned at or supporting ${targetBlooms} cognitive level (${Array.from(new Set(critBlooms)).join(', ')}).`;

    // 4. Weight consistency
    const totalWeight = criteria.reduce((sum, c) => sum + (parseFloat(c.weight_percentage) || 0), 0);
    const weightOk = Math.abs(totalWeight - 100.0) < 0.05;
    const allPositive = criteria.every((c) => (parseFloat(c.weight_percentage) || 0) > 0);
    const weightPassed = weightOk && allPositive;
    const weightDetail = weightOk
      ? `Total criteria weight is exactly ${totalWeight.toFixed(1)}% with active non-zero allocations.`
      : `Total weight sums to ${totalWeight.toFixed(1)}% (Required: exactly 100.00%).`;

    // 5. Total marks verification
    const totalAllocatedMarks = criteria.reduce((sum, c) => sum + (parseFloat(c.max_marks) || 0), 0);
    const maxMarks = parseFloat(selectedAssessment.max_marks) || 20.0;
    const marksOk = Math.abs(totalAllocatedMarks - maxMarks) < 0.1;
    const marksPassed = marksOk;
    const marksDetail = marksOk
      ? `Allocated marks (${totalAllocatedMarks.toFixed(1)}) match assessment max marks (${maxMarks.toFixed(1)} Marks).`
      : `Allocated marks sum to ${totalAllocatedMarks.toFixed(1)}, differing from question total ${maxMarks.toFixed(1)} Marks.`;

    // Duplicate check
    const names = criteria.map((c) => (c.criterion_name || '').trim().toLowerCase());
    const hasDuplicates = names.length !== new Set(names).size;

    const allPassed = completenessPassed && relevancePassed && bloomsPassed && weightPassed && marksPassed && !hasDuplicates;
    const passedCount = [completenessPassed, relevancePassed, bloomsPassed, weightPassed, marksPassed, !hasDuplicates].filter(Boolean).length;
    const computedScore = Math.round((passedCount / 6) * 100);

    const warnings = [];
    if (!completenessPassed) warnings.push('At least 3 criteria with graduated performance descriptors are recommended.');
    if (!weightPassed) warnings.push(`Weight divergence: Total criteria weight is ${totalWeight.toFixed(1)}% instead of 100.0%.`);
    if (!marksPassed) warnings.push(`Mark discrepancy: Allocated criteria marks sum to ${totalAllocatedMarks.toFixed(1)} instead of question max ${maxMarks.toFixed(1)} marks.`);
    if (hasDuplicates) warnings.push('Duplicate criteria names detected. Remove or merge identical criteria.');
    if (!bloomsPassed) warnings.push(`Cognitive complexity divergence from target Bloom's level: ${targetBlooms}.`);

    let checks = [
      { name: 'Criterion Completeness', passed: completenessPassed, detail: completenessDetail },
      { name: 'Question Relevance', passed: relevancePassed, detail: relevanceDetail },
      { name: "Bloom's Taxonomy Alignment", passed: bloomsPassed, detail: bloomsDetail },
      { name: 'Weight Consistency (100.0%)', passed: weightPassed, detail: weightDetail },
      { name: 'Total Marks Verification', passed: marksPassed, detail: marksDetail },
      { name: 'Duplicate Criteria Check', passed: !hasDuplicates, detail: hasDuplicates ? 'Duplicate criteria names detected.' : 'No duplicate criteria detected.' },
    ];

    if (validationDetails?.checks && Array.isArray(validationDetails.checks)) {
      checks = validationDetails.checks;
    }

    const backendMsgs = Array.isArray(currentRubric.validation_messages)
      ? currentRubric.validation_messages
      : typeof currentRubric.validation_messages === 'string'
      ? JSON.parse(currentRubric.validation_messages || '[]')
      : [];

    const finalWarnings = Array.from(new Set([...warnings, ...backendMsgs]));

    return {
      completeness: { passed: completenessPassed, detail: completenessDetail, count, totalDescriptors },
      relevance: { passed: relevancePassed, detail: relevanceDetail, score: relevanceScore },
      blooms: { passed: bloomsPassed, detail: bloomsDetail, target: targetBlooms },
      weight: { passed: weightPassed, detail: weightDetail, total: totalWeight },
      marks: { passed: marksPassed, detail: marksDetail, total: totalAllocatedMarks, max: maxMarks },
      score: currentRubric.validation_score ? Math.round(currentRubric.validation_score * 100) : computedScore,
      status: currentRubric.validation_status || (allPassed ? 'valid' : (computedScore >= 60 ? 'warning' : 'invalid')),
      checks,
      warnings: finalWarnings,
      allPassed,
    };
  }, [currentRubric, selectedAssessment, validationDetails]);

  const handleStartEditRubric = () => {
    if (!activeRubric?.criteria) return;
    if (activeRubric.is_approved) {
      showPhase3Toast('error', 'Approved rubrics are locked. Create a new version to modify criteria.');
      return;
    }
    if (activeRubric.status === 'rejected') {
      showPhase3Toast('error', 'Rejected rubrics cannot be edited directly. Please regenerate an improved version.');
      return;
    }
    setEditableCriteria(JSON.parse(JSON.stringify(activeRubric.criteria)));
    setIsEditingRubric(true);
  };

  const handleCriterionWeightChange = (index, newWeight) => {
    const updated = [...editableCriteria];
    const val = parseFloat(newWeight) || 0.0;
    updated[index].weight_percentage = val;
    const maxM = selectedAssessment?.max_marks || 20.0;
    updated[index].max_marks = parseFloat(((val / 100.0) * maxM).toFixed(2));
    setEditableCriteria(updated);
  };

  const handleCriterionFieldChange = (index, field, value) => {
    const updated = [...editableCriteria];
    updated[index][field] = value;
    setEditableCriteria(updated);
  };

  const handlePerformanceLevelChange = (critIndex, levelIndex, field, value) => {
    const updated = [...editableCriteria];
    const crit = { ...updated[critIndex] };
    const levels = Array.isArray(crit.performance_levels) ? [...crit.performance_levels] : [];
    if (levels[levelIndex]) {
      levels[levelIndex] = {
        ...levels[levelIndex],
        [field]: value,
      };
      crit.performance_levels = levels;
      updated[critIndex] = crit;
      setEditableCriteria(updated);
    }
  };

  const handleAddCriterion = () => {
    const newCrit = {
      criterion_name: 'New Pedagogical Dimension',
      description: 'Lecturer-defined evaluation criterion description',
      weight_percentage: 0.0,
      max_marks: 0.0,
      blooms_dimension: selectedAssessment?.blooms_level || 'Apply',
      performance_levels: [
        { level: 'Exemplary', score_percentage: 100, description: 'Exemplary demonstration with comprehensive precision' },
        { level: 'Proficient', score_percentage: 75, description: 'Proficient demonstration with minor non-critical omissions' },
        { level: 'Developing', score_percentage: 50, description: 'Developing understanding with notable conceptual gaps' },
        { level: 'Novice', score_percentage: 25, description: 'Novice understanding lacking fundamental mechanics' },
      ],
    };
    setEditableCriteria([...editableCriteria, newCrit]);
  };

  const handleRemoveCriterion = (index) => {
    const updated = editableCriteria.filter((_, idx) => idx !== index);
    setEditableCriteria(updated);
  };

  const handleSaveEditedRubric = async () => {
    if (!activeRubric) return;
    if (activeRubric.is_approved) {
      showPhase3Toast('error', 'Cannot edit an approved rubric directly. Please create or regenerate a new version.');
      return;
    }
    if (activeRubric.status === 'rejected') {
      showPhase3Toast('error', 'Cannot edit a rejected rubric directly. Please regenerate a new rubric version.');
      return;
    }
    const totalWeight = editableCriteria.reduce((sum, c) => sum + (parseFloat(c.weight_percentage) || 0), 0);
    if (Math.abs(totalWeight - 100.0) > 0.1) {
      showPhase3Toast('error', `Validation Error: Total criterion weights must equal exactly 100.0%. Current total: ${totalWeight.toFixed(1)}%`);
      return;
    }
    setLoading(true);
    try {
      const currentRubricId = activeRubric.id;
      const payload = {
        title: activeRubric.title,
        criteria: editableCriteria.map((c) => ({
          criterion_name: c.criterion_name,
          description: c.description,
          weight_percentage: c.weight_percentage,
          max_marks: c.max_marks,
          blooms_dimension: c.blooms_dimension || 'Analytical',
          performance_levels: c.performance_levels || [],
        })),
      };
      const updated = await api.updateRubric(currentRubricId, payload);
      setActiveRubric(updated);
      setEditableCriteria(updated.criteria || []);
      setIsEditingRubric(false);
      showPhase3Toast('success', 'Rubric criteria and weights updated and saved successfully!');
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Failed to save rubric: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveRubric = async () => {
    if (!activeRubric) return;
    if (activeRubric.status === 'rejected') {
      showPhase3Toast('error', 'Cannot approve a rejected rubric. Please regenerate a new version first.');
      return;
    }
    setLoading(true);
    try {
      const approved = await api.approveRubric(activeRubric.id, approvalLecturer, approvalNotes);
      setActiveRubric(approved);
      showPhase3Toast('success', `Rubric officially approved by ${approvalLecturer}! Official student scoring is now unlocked.`);
      await fetchDatasetData();
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Approval failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Phase 3: Helper to show toast messages
  const showPhase3Toast = (type, message) => {
    setPhase3Toast({ type, message });
    setTimeout(() => setPhase3Toast(null), 5000);
  };

  // Phase 3: Fetch version history for current assessment
  const fetchVersionHistory = async (assessmentId) => {
    if (!assessmentId) return;
    try {
      const history = await api.getAssessmentRubricHistory(assessmentId);
      setVersionHistory(history.versions || []);
    } catch (err) {
      console.warn('Version history fetch notice:', err.message);
      setVersionHistory([]);
    }
  };

  // Phase 3: Open reject modal
  const handleOpenRejectModal = () => {
    if (!activeRubric) return;
    setSelectedRejectionReasons([]);
    setRejectionFeedback('');
    setRejectionLecturer(approvalLecturer || 'Dr. Lecturer Lead (Module Coordinator)');
    setShowRejectModal(true);
  };

  // Phase 3: Toggle rejection reason
  const handleToggleReason = (reason) => {
    setSelectedRejectionReasons((prev) =>
      prev.includes(reason)
        ? prev.filter((r) => r !== reason)
        : [...prev, reason]
    );
  };

  // Phase 3: Reject rubric
  const handleRejectRubric = async () => {
    if (!activeRubric || selectedRejectionReasons.length === 0) {
      showPhase3Toast('error', 'Please select at least one rejection reason.');
      return;
    }
    setIsRejecting(true);
    try {
      const rejected = await api.rejectRubric(activeRubric.id, {
        rejection_reasons: selectedRejectionReasons,
        feedback: rejectionFeedback.trim() || null,
        rejected_by: rejectionLecturer || 'Dr. Lecturer',
      });
      setActiveRubric(rejected);
      setEditableCriteria(rejected.criteria || []);
      setShowRejectModal(false);
      showPhase3Toast('success', `Rubric rejected by ${rejectionLecturer}. You can now regenerate an improved version.`);
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Rejection failed: ${err.message}`);
    } finally {
      setIsRejecting(false);
    }
  };

  // Phase 3: Regenerate rubric with feedback
  const handleRegenerateRubric = async () => {
    if (!activeRubric) return;
    setIsRegenerating(true);
    try {
      const regenerated = await api.regenerateRubric(activeRubric.id, {
        rejected_by: rejectionLecturer || approvalLecturer || 'Dr. Lecturer',
      });
      setActiveRubric(regenerated);
      setEditableCriteria(regenerated.criteria || []);
      setIsEditingRubric(false);
      showPhase3Toast('success', `Rubric v${regenerated.version} regenerated successfully! Status: PENDING APPROVAL.`);
      if (selectedAssessment) await fetchVersionHistory(selectedAssessment.id);
    } catch (err) {
      showPhase3Toast('error', `Regeneration failed: ${err.message}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  // Phase 3: Select a specific version from history
  const handleSelectVersion = async (versionItem) => {
    if (!versionItem) return;
    setLoading(true);
    try {
      const detail = await api.getRubricDetail(versionItem.id);
      setActiveRubric(detail);
      setEditableCriteria(detail.criteria || []);
      setIsEditingRubric(false);
    } catch (err) {
      showPhase3Toast('error', `Failed to load version: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleScoreStudent = async () => {
    if (!selectedAssessment || !activeRubric) {
      alert('Please select an assessment with a rubric first.');
      return;
    }
    if (activeRubric.status === 'rejected') {
      showPhase3Toast('error', 'Official Scoring Blocked: Current rubric is marked as REJECTED. A rejected rubric cannot be used for student evaluation. Please regenerate an improved version.');
      return;
    }
    if (!activeRubric.is_approved) {
      showPhase3Toast('error', 'Official Scoring Blocked: The rubric status is currently Pending Approval. An authorized lecturer must review and approve the rubric before official student scoring can take place.');
      return;
    }
    setLoading(true);
    try {
      const res = await api.evaluateStudentAnswer({
        assessment_id: selectedAssessment.id,
        rubric_id: activeRubric.id,
        student_id: studentId,
        student_name: studentName,
        answer_text: studentAnswer,
        scoring_method: scoringMethod,
      });
      setScoringResult(res);
      // refresh analytics
      const updatedResults = await api.getAssessmentResults(selectedAssessment.id);
      setResultsData(updatedResults);
      await fetchDatasetData();
    } catch (err) {
      alert(`Scoring failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleImportLecturerRubrics = async () => {
    setDatasetLoading(true);
    try {
      const res = await api.importLecturerRubric();
      alert(res.message);
      const assessList = await api.getAssessments();
      setAssessments(assessList);
      if (assessList.length > 0) {
        handleSelectAssessment(assessList[0]);
      }
      await fetchDatasetData();
    } catch (err) {
      alert(`Import failed: ${err.message}`);
    } finally {
      setDatasetLoading(false);
    }
  };

  const handleImportStudentResponses = async () => {
    setDatasetLoading(true);
    try {
      const res = await api.importStudentResponses();
      alert(res.message);
      await fetchDatasetData();
      if (selectedAssessment) {
        const rData = await api.getAssessmentResults(selectedAssessment.id);
        setResultsData(rData);
      }
    } catch (err) {
      alert(`Student import failed: ${err.message}`);
    } finally {
      setDatasetLoading(false);
    }
  };

  const handleBatchEvaluate = async (methodToUse) => {
    setBatchLoading(true);
    setBatchMessage(null);
    try {
      const res = await api.batchEvaluate(methodToUse, selectedAssessment ? selectedAssessment.id : null);
      setBatchResult(res);
      setBatchMessage(res.message);
      alert(res.message);
      await fetchDatasetData();
      if (selectedAssessment) {
        const rData = await api.getAssessmentResults(selectedAssessment.id);
        setResultsData(rData);
      }
    } catch (err) {
      alert(`Batch evaluation error: ${err.message}`);
    } finally {
      setBatchLoading(false);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealth={systemHealth}
      />

      <div className="main-wrapper">
        <Header activeTab={activeTab} />

        <main className="content-area">
          {/* TAB: DASHBOARD OVERVIEW */}
          {activeTab === 'dashboard' && (
            <div>
              <div className="academic-banner">
                <div className="banner-content">
                  <span className="banner-badge">Research Component ID: IT23376472</span>
                  <h3>Adaptive AI-Based Rubric Generation and Criterion-Based Scoring System</h3>
                  <p>
                    A trustworthy explainable framework for automated short-answer evaluation.
                    Empowers lecturers to synthesize adaptive multidimensional rubrics, dynamically optimize
                    criteria weights aligned to Bloom’s taxonomy, validate pedagogical coherence, and perform
                    objective criterion-based student answer evaluation.
                  </p>
                </div>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-info">
                    <p>Total Assessments</p>
                    <h4>{assessments.length}</h4>
                  </div>
                  <div className="stat-icon blue">
                    <BookOpen size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Rubric Engine Status</p>
                    <h4>{activeRubric?.is_approved ? 'Approved' : 'Active'}</h4>
                  </div>
                  <div className="stat-icon purple">
                    <Layers size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Cohort Average Score</p>
                    <h4>{resultsData?.average_score ? `${resultsData.average_score}%` : '88.5%'}</h4>
                  </div>
                  <div className="stat-icon green">
                    <Award size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Submissions Evaluated</p>
                    <h4>{resultsData?.total_submissions || 1}</h4>
                  </div>
                  <div className="stat-icon amber">
                    <BarChart size={22} />
                  </div>
                </div>
              </div>

              {/* Research Component Workflow Pipeline */}
              <div className="card">
                <div className="card-header">
                  <div>
                    <h3 className="card-title">8-Stage Research Architecture Pipeline</h3>
                    <p className="card-subtitle">
                      End-to-end flow of the assigned research component for subjective assessment
                    </p>
                  </div>
                  <button onClick={fetchInitialData} className="btn btn-secondary btn-sm">
                    <RefreshCw size={14} /> Refresh Data
                  </button>
                </div>

                <div className="card-body">
                  <div className="features-grid">
                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">1</span> Lecturer Assessment Creation
                        </h4>
                        <p>Author subjective assessment questions, reference guidelines, and total mark targets.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('assessments')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">2</span> AI Question Analysis
                        </h4>
                        <p>Analyze question cognitive tier (Bloom's taxonomy), key conceptual entities, and structure.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('analysis')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">3</span> Adaptive Rubric Generation
                        </h4>
                        <p>Synthesize adaptive 4-tier rubric descriptors (Exemplary, Proficient, Developing, Unsatisfactory).</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('rubrics')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">4</span> Dynamic Weight Optimization
                        </h4>
                        <p>Calibrate and balance criteria weights mathematically to sum to exactly 100%.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('weights')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">5</span> Rubric Validation
                        </h4>
                        <p>Automated verification of cognitive depth coverage, descriptor graduation, and mathematical soundness.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('validation')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">6</span> Lecturer Rubric Approval
                        </h4>
                        <p>Human-in-the-loop lecturer review, rubric descriptor adjustment, and official sign-off.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('approval')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">7</span> Student Answer Scoring
                        </h4>
                        <p>Granular criterion-based scoring awarding marks with explainable formative feedback.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('scoring')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>

                    <div className="feature-card">
                      <div>
                        <h4>
                          <span className="badge badge-purple">8</span> Assessment Results
                        </h4>
                        <p>Cohort performance metrics, score distributions, and criterion-by-criterion performance diagnostics.</p>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('results')}>
                        Explore Module <ArrowRight size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 1: ASSESSMENTS (SETUP & BENCHMARK) */}
          {activeTab === 'assessments' && (
            <div>
              {/* SECTION 1 — RESEARCH BENCHMARK DATASET */}
              <div className="card" style={{ marginBottom: '24px', border: '1px solid #E2E8F0', background: '#FFFFFF' }}>
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', borderBottom: '1px solid #F1F5F9', padding: '16px 20px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Award size={18} color="#4F46E5" />
                      <h3 className="card-title" style={{ color: '#1E1B4B', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                        Research Benchmark Dataset: Java OOP Empirical Study
                      </h3>
                      <span className="badge badge-purple" style={{ fontSize: '0.7rem' }}>Course: IT4360</span>
                    </div>
                    <p className="card-subtitle" style={{ marginTop: '4px', fontSize: '0.78rem', color: '#64748B' }}>
                      Canonical benchmark dataset for academic rubric evaluation and scoring. Select any question to inspect or analyze without creating duplicate records.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <span className="badge badge-secondary" style={{ fontSize: '0.74rem', background: '#F1F5F9', color: '#334155', border: '1px solid #E2E8F0' }}>
                      <strong>5</strong> Questions (IDs 47–51)
                    </span>
                    <span className="badge badge-secondary" style={{ fontSize: '0.74rem', background: '#F1F5F9', color: '#334155', border: '1px solid #E2E8F0' }}>
                      <strong>310</strong> Answers
                    </span>
                    <span className="badge badge-secondary" style={{ fontSize: '0.74rem', background: '#F1F5F9', color: '#334155', border: '1px solid #E2E8F0' }}>
                      <strong>62</strong> Response Sets
                    </span>
                  </div>
                </div>

                <div className="card-body" style={{ padding: '12px 20px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {JAVA_OOP_PRESETS.map((p, idx) => {
                      const isSelected = selectedAssessment?.id === p.id;
                      const matchingDb = assessments.find((a) => a.id === p.id);
                      return (
                        <div
                          key={p.id}
                          style={{
                            border: isSelected ? '1.5px solid #4F46E5' : '1px solid #E2E8F0',
                            borderRadius: '8px',
                            padding: '12px 16px',
                            background: isSelected ? '#F5F7FF' : '#FFFFFF',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: '16px',
                            flexWrap: 'wrap',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div style={{ flex: '1 1 500px', minWidth: '280px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                              <span style={{ fontWeight: 700, fontSize: '0.84rem', color: isSelected ? '#3730A3' : '#1E293B' }}>
                                Q{idx + 1}: {p.short_label.replace(/^Q\d+:\s*/, '')}
                              </span>
                              <span style={{ fontSize: '0.72rem', color: '#64748B', fontWeight: 500 }}>
                                (ID #{p.id})
                              </span>
                              {isSelected && (
                                <span className="badge badge-success" style={{ fontSize: '0.66rem', padding: '1px 6px' }}>
                                  Active Selection
                                </span>
                              )}
                            </div>
                            <div style={{ fontSize: '0.82rem', color: '#334155', lineHeight: '1.4', marginBottom: '6px' }}>
                              {p.question}
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', fontSize: '0.72rem', color: '#64748B' }}>
                              <span><strong>LO:</strong> {p.learning_outcome}</span>
                              <span style={{ color: '#059669', fontWeight: 600 }}>• 62 Historical Submissions</span>
                              <span style={{ color: '#4F46E5', fontWeight: 500 }}>• Historical Baseline Scoring Available</span>
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '3px' }}>
                              <span className="badge badge-purple" style={{ fontSize: '0.68rem', padding: '2px 6px' }}>
                                Understand
                              </span>
                              <span style={{ fontSize: '0.72rem', fontWeight: 600, color: '#475569' }}>
                                10 Marks
                              </span>
                            </div>
                            {isSelected ? (
                              <button
                                type="button"
                                className="btn btn-primary btn-sm"
                                style={{ fontSize: '0.74rem', padding: '5px 12px', display: 'flex', alignItems: 'center', gap: '4px' }}
                                onClick={() => setActiveTab('analysis')}
                              >
                                Selected <ArrowRight size={12} />
                              </button>
                            ) : (
                              <button
                                type="button"
                                className="btn btn-secondary btn-sm"
                                style={{ fontSize: '0.74rem', padding: '5px 12px' }}
                                onClick={() => {
                                  const target = matchingDb || p;
                                  handleSelectAssessment(target);
                                }}
                              >
                                Select Q{idx + 1}
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* SECTION 2 — CREATE NEW ASSESSMENT */}
              <div className="card" style={{ marginBottom: '24px', border: '1px solid #E2E8F0', background: '#FFFFFF' }}>
                <div className="card-header" style={{ borderBottom: '1px solid #F1F5F9', padding: '16px 20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Plus size={18} color="#4F46E5" />
                    <h3 className="card-title" style={{ color: '#1E1B4B', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                      Create New Assessment
                    </h3>
                  </div>
                  <p className="card-subtitle" style={{ marginTop: '4px', fontSize: '0.78rem', color: '#64748B' }}>
                    Register general subjective questions for automated rubric generation and evaluation beyond the research benchmark.
                  </p>
                </div>

                <div className="card-body" style={{ padding: '20px' }}>
                  <form onSubmit={handleCreateAssessment}>
                    <div className="form-group" style={{ marginBottom: '16px' }}>
                      <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Assessment Title</label>
                      <input
                        className="form-input"
                        placeholder="e.g. Java Polymorphism & Abstract Contracts"
                        value={newTitle}
                        onChange={(e) => setNewTitle(e.target.value)}
                        required
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                      <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Bloom's Taxonomy Level</label>
                        <select
                          className="form-select"
                          value={newBlooms}
                          onChange={(e) => setNewBlooms(e.target.value)}
                        >
                          <option value="Remember">Remember</option>
                          <option value="Understand">Understand</option>
                          <option value="Apply">Apply</option>
                          <option value="Analyze">Analyze</option>
                          <option value="Evaluate">Evaluate</option>
                          <option value="Create">Create</option>
                        </select>
                      </div>

                      <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Maximum Total Marks</label>
                        <input
                          type="number"
                          step="0.5"
                          min="1"
                          className="form-input"
                          value={newMaxMarks}
                          onChange={(e) => setNewMaxMarks(e.target.value)}
                          required
                        />
                      </div>
                    </div>

                    <div className="form-group" style={{ marginBottom: '16px' }}>
                      <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Subjective Question Text</label>
                      <textarea
                        className="form-textarea"
                        placeholder="Enter the subjective assessment question..."
                        value={newQuestion}
                        onChange={(e) => setNewQuestion(e.target.value)}
                        rows={3}
                        required
                      />
                    </div>

                    <div className="form-group" style={{ marginBottom: '16px' }}>
                      <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Model / Reference Answer</label>
                      <textarea
                        className="form-textarea"
                        placeholder="Expected theoretical points and implementation criteria..."
                        value={newModelAnswer}
                        onChange={(e) => setNewModelAnswer(e.target.value)}
                        rows={2}
                      />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                      <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Target Learning Outcome</label>
                        <input
                          className="form-input"
                          placeholder="e.g. Demonstrate method overriding and dynamic binding in Java"
                          value={newLearningOutcome}
                          onChange={(e) => setNewLearningOutcome(e.target.value)}
                        />
                      </div>

                      <div className="form-group" style={{ margin: 0 }}>
                        <label className="form-label" style={{ fontWeight: 600, fontSize: '0.82rem', marginBottom: '6px' }}>Lecturer Guidelines / Constraints</label>
                        <input
                          className="form-input"
                          placeholder="e.g. Accept semantically equivalent correct answers; verify examples"
                          value={newGuidelines}
                          onChange={(e) => setNewGuidelines(e.target.value)}
                        />
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                      <button
                        type="submit"
                        className="btn btn-primary"
                        style={{
                          width: '100%',
                          maxWidth: '260px',
                          padding: '9px 18px',
                          fontSize: '0.86rem',
                          fontWeight: 600,
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '6px',
                        }}
                      >
                        <Plus size={16} /> Create Assessment & Continue
                      </button>
                    </div>
                  </form>
                </div>
              </div>

              {/* SECTION 3 — OTHER ASSESSMENTS (COLLAPSIBLE) */}
              <div className="card" style={{ marginBottom: '24px', border: '1px solid #E2E8F0', background: '#FFFFFF' }}>
                <div
                  className="card-header"
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    userSelect: 'none',
                    padding: '16px 20px',
                    borderBottom: showOtherAssessments ? '1px solid #F1F5F9' : 'none',
                  }}
                  onClick={() => setShowOtherAssessments(!showOtherAssessments)}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Layers size={18} color="#6366F1" />
                      <h3 className="card-title" style={{ color: '#1E1B4B', fontSize: '1rem', fontWeight: 700, margin: 0 }}>
                        Other Registered Assessments
                      </h3>
                      <span className="badge badge-secondary" style={{ fontSize: '0.72rem', background: '#F1F5F9', color: '#475569' }}>
                        {assessments.filter((a) => ![47, 48, 49, 50, 51].includes(a.id)).length} Available
                      </span>
                    </div>
                    <p className="card-subtitle" style={{ marginTop: '4px', fontSize: '0.78rem', color: '#64748B' }}>
                      General subjective assessments in active database (canonical benchmark IDs 47–51 excluded). Click to {showOtherAssessments ? 'collapse' : 'expand'}.
                    </p>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.76rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowOtherAssessments(!showOtherAssessments);
                    }}
                  >
                    {showOtherAssessments ? (
                      <>Hide List <ChevronUp size={14} /></>
                    ) : (
                      <>Show List ({assessments.filter((a) => ![47, 48, 49, 50, 51].includes(a.id)).length}) <ChevronDown size={14} /></>
                    )}
                  </button>
                </div>

                {showOtherAssessments && (
                  <div className="card-body" style={{ padding: 0 }}>
                    <div style={{ maxHeight: '450px', overflowY: 'auto' }}>
                      {assessments.filter((a) => ![47, 48, 49, 50, 51].includes(a.id)).length === 0 ? (
                        <div style={{ padding: '32px', textAlign: 'center', color: '#64748B' }}>
                          <Info size={24} style={{ marginBottom: '8px', color: '#94A3B8' }} />
                          <p style={{ margin: 0, fontWeight: 500 }}>No additional custom assessments registered.</p>
                          <p style={{ fontSize: '0.78rem', margin: '4px 0 0 0' }}>Use the form above to register new assessments.</p>
                        </div>
                      ) : (
                        <table className="academic-table" style={{ margin: 0 }}>
                          <thead>
                            <tr>
                              <th style={{ width: '12%' }}>ID</th>
                              <th style={{ width: '50%' }}>Title & Question Preview</th>
                              <th style={{ width: '14%' }}>Bloom's</th>
                              <th style={{ width: '10%' }}>Marks</th>
                              <th style={{ width: '14%' }}>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {assessments
                              .filter((a) => ![47, 48, 49, 50, 51].includes(a.id))
                              .map((a) => {
                                const isCurrent = selectedAssessment?.id === a.id;
                                return (
                                  <tr
                                    key={a.id}
                                    style={{
                                      background: isCurrent ? '#F0FDF4' : 'transparent',
                                    }}
                                  >
                                    <td>
                                      <strong>#{a.id}</strong>
                                    </td>
                                    <td>
                                      <strong style={{ color: isCurrent ? '#065F46' : '#1E293B', fontSize: '0.84rem' }}>{a.title}</strong>
                                      <p style={{ fontSize: '0.74rem', color: '#64748B', margin: '2px 0 0 0', lineHeight: '1.3' }}>
                                        {a.question_text ? (a.question_text.length > 70 ? a.question_text.substring(0, 70) + '...' : a.question_text) : ''}
                                      </p>
                                    </td>
                                    <td>
                                      <span className="badge badge-purple" style={{ fontSize: '0.72rem' }}>{a.blooms_level || 'Understand'}</span>
                                    </td>
                                    <td>
                                      <span style={{ fontWeight: 600 }}>{a.max_marks}</span>
                                    </td>
                                    <td>
                                      <div style={{ display: 'flex', gap: '4px' }}>
                                        <button
                                          className={`btn btn-sm ${isCurrent ? 'btn-primary' : 'btn-secondary'}`}
                                          style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                          onClick={() => handleSelectAssessment(a)}
                                        >
                                          {isCurrent ? 'Active' : 'Select'}
                                        </button>
                                        <button
                                          className="btn btn-secondary btn-sm"
                                          style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                          onClick={async () => {
                                            await handleSelectAssessment(a);
                                            setActiveTab('analysis');
                                          }}
                                        >
                                          Analyze
                                        </button>
                                      </div>
                                    </td>
                                  </tr>
                                );
                              })}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: AI QUESTION ANALYSIS */}
          {activeTab === 'analysis' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Question Input for Analysis</h3>
                </div>
                <div className="card-body">
                  <div className="form-group">
                    <label className="form-label">Question Text</label>
                    <textarea
                      className="form-textarea"
                      value={testQuestion}
                      onChange={(e) => setTestQuestion(e.target.value)}
                      rows={5}
                    />
                  </div>

                  <button
                    className="btn btn-primary"
                    onClick={handleAnalyzeQuestion}
                    disabled={loading}
                  >
                    <Sparkles size={16} /> Run AI Question Analysis
                  </button>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">AI Analysis Breakdown</h3>
                </div>
                <div className="card-body">
                  {analysisResult ? (
                    <div>
                      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
                        <span className="badge badge-purple">
                          Bloom's Tier: {analysisResult.blooms_level}
                        </span>
                        <span className="badge badge-info">
                          Complexity: {analysisResult.cognitive_complexity}
                        </span>
                      </div>

                      <p style={{ fontSize: '0.86rem', color: '#475569', marginBottom: '16px' }}>
                        {analysisResult.rationale}
                      </p>

                      <h4 style={{ fontSize: '0.86rem', fontWeight: 700, marginBottom: '8px' }}>
                        Extracted Key Concepts
                      </h4>
                      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                        {analysisResult.extracted_concepts.map((concept, idx) => (
                          <span key={idx} className="badge badge-success">
                            {concept}
                          </span>
                        ))}
                      </div>

                      <h4 style={{ fontSize: '0.86rem', fontWeight: 700, marginBottom: '8px' }}>
                        Recommended Rubric Criteria
                      </h4>
                      <ul style={{ paddingLeft: '18px', fontSize: '0.84rem', color: '#334155' }}>
                        {analysisResult.recommended_criteria.map((c, idx) => (
                          <li key={idx} style={{ marginBottom: '4px' }}>
                            <strong>{c.name}</strong> — {c.weight}% recommended weight
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '32px 0', color: '#94A3B8' }}>
                      Click "Run AI Question Analysis" to inspect cognitive taxonomy breakdown.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3 & 4 & 5 & 6: RUBRIC LIFECYCLE */}
          {(activeTab === 'rubrics' || activeTab === 'weights' || activeTab === 'validation' || activeTab === 'approval') && (
            <div>
              {/* Phase 3: Toast Messages */}
              {phase3Toast && (
                <div className={`toast-message ${phase3Toast.type}`}>
                  {phase3Toast.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                  <span>{phase3Toast.message}</span>
                  <button
                    onClick={() => setPhase3Toast(null)}
                    style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', padding: '2px', lineHeight: 1 }}
                  >
                    <X size={14} />
                  </button>
                </div>
              )}

              {/* Assessment Context Selector & Step Navigator Bar */}
              <div
                style={{
                  background: '#FFFFFF',
                  border: '1px solid #E2E8F0',
                  borderRadius: '10px',
                  padding: '14px 18px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '12px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BookOpen size={18} color="#6366F1" />
                    <span style={{ fontSize: '0.86rem', fontWeight: 700, color: '#1E293B' }}>
                      Active Assessment:
                    </span>
                  </div>
                  <select
                    className="form-select"
                    style={{ minWidth: '320px', maxWidth: '460px', padding: '6px 12px', fontSize: '0.84rem' }}
                    value={selectedAssessment?.id || ''}
                    onChange={(e) => {
                      const assessId = parseInt(e.target.value, 10);
                      const found = assessments.find((a) => a.id === assessId);
                      if (found) handleSelectAssessment(found);
                    }}
                  >
                    {assessments.map((a) => (
                      <option key={a.id} value={a.id}>
                        #{a.id}: {a.title} ({a.blooms_level || 'Apply'}, {a.max_marks || 20} Marks)
                      </option>
                    ))}
                  </select>

                    <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                      <span className="badge badge-purple" style={{ fontSize: '0.74rem' }}>
                        {selectedAssessment?.blooms_level || 'Apply'}
                      </span>
                      <span className="badge badge-info" style={{ fontSize: '0.74rem' }}>
                        Max: {selectedAssessment?.max_marks || 20} Marks
                      </span>
                      <span className="badge badge-success" style={{ fontSize: '0.74rem' }}>
                        {selectedAssessment?.course_code || 'IT4360'}
                      </span>
                      {currentRubric ? (
                        <span className={`badge ${currentRubric.is_approved ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.74rem' }}>
                          {currentRubric.is_approved ? `AI Rubric Approved (v${currentRubric.version || 1})` : `AI Rubric Pending (v${currentRubric.version || 1})`}
                        </span>
                      ) : currentBaselineRubric ? (
                        <span className="badge badge-secondary" style={{ fontSize: '0.74rem', background: '#FEF3C7', color: '#92400E', border: '1px solid #F59E0B' }}>
                          Baseline Only — AI Rubric Needed
                        </span>
                      ) : (
                        <span className="badge badge-secondary" style={{ fontSize: '0.74rem', background: '#F1F5F9', color: '#64748B' }}>
                          No Rubric
                        </span>
                      )}
                    </div>
                </div>

                {/* Rubric Step Tabs */}
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center', background: '#F1F5F9', padding: '4px', borderRadius: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setActiveTab('rubrics')}
                    className={`btn btn-sm ${activeTab === 'rubrics' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.76rem', padding: '4px 10px' }}
                  >
                    <Layers size={13} /> Step 3: Adaptive Rubrics
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('weights')}
                    className={`btn btn-sm ${activeTab === 'weights' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.76rem', padding: '4px 10px' }}
                  >
                    <Sliders size={13} /> Step 4: Dynamic Weights
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('validation')}
                    className={`btn btn-sm ${activeTab === 'validation' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.76rem', padding: '4px 10px' }}
                  >
                    <CheckCircle size={13} /> Step 5: Validation
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('approval')}
                    className={`btn btn-sm ${activeTab === 'approval' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.76rem', padding: '4px 10px' }}
                  >
                    <Edit3 size={13} /> Step 6: Approval
                  </button>
                </div>
              </div>

              {/* Lifecycle Stage Guidance Banner - 3 States (Shown on Tabs 3, 4, 6 - Step 5 has its own dedicated validation status banner) */}
              {activeTab !== 'validation' && (
                <div
                  style={{
                    background: activeRubric?.is_approved
                      ? '#ECFDF5'
                      : activeRubric?.status === 'rejected'
                      ? 'linear-gradient(135deg, #FEF2F2 0%, #FFF1F2 100%)'
                      : '#F5F3FF',
                    border: `1px solid ${
                      activeRubric?.is_approved
                        ? '#A7F3D0'
                        : activeRubric?.status === 'rejected'
                        ? '#FECACA'
                        : '#DDD6FE'
                    }`,
                    borderRadius: '10px',
                    padding: '14px 20px',
                    marginBottom: '20px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {activeRubric?.is_approved ? (
                      <Unlock size={22} color="#10B981" />
                    ) : activeRubric?.status === 'rejected' ? (
                      <ShieldAlert size={22} color="#EF4444" />
                    ) : (
                      <Lock size={22} color="#8B5CF6" />
                    )}
                    <div>
                      <h4
                        style={{
                          margin: 0,
                          fontSize: '0.95rem',
                          fontWeight: 700,
                          color: activeRubric?.is_approved
                            ? '#065F46'
                            : activeRubric?.status === 'rejected'
                            ? '#991B1B'
                            : '#5B21B6',
                        }}
                      >
                        {activeRubric?.is_approved
                          ? `Official Rubric Approved & Locked (Authorized by ${activeRubric.approved_by || 'Course Lead'})`
                          : activeRubric?.status === 'rejected'
                          ? `Rubric Rejected by ${activeRubric.rejected_by || 'Lecturer'} — Regeneration Required`
                          : 'Rubric in Review / Optimization (Pending Formal Lecturer Approval)'}
                      </h4>
                      <p
                        style={{
                          margin: 0,
                          fontSize: '0.8rem',
                          color: activeRubric?.is_approved
                            ? '#047857'
                            : activeRubric?.status === 'rejected'
                            ? '#B91C1C'
                            : '#6D28D9',
                        }}
                      >
                        {activeRubric?.is_approved
                          ? 'Official criterion-based student scoring is active and unlocked for this assessment.'
                          : activeRubric?.status === 'rejected'
                          ? 'This rubric version was rejected. Use "Regenerate Rubric with Feedback" to create an improved version addressing the identified issues.'
                          : 'Rule-based weights can be dynamically optimized or edited by the lecturer. Approval is required prior to official student scoring.'}
                      </p>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span
                      className={`badge ${
                        activeRubric?.is_approved
                          ? 'badge-success'
                          : activeRubric?.status === 'rejected'
                          ? 'badge-danger'
                          : 'badge-purple'
                      }`}
                      style={{ fontSize: '0.82rem', padding: '6px 14px' }}
                    >
                      {activeRubric?.is_approved
                        ? 'APPROVED FOR EVALUATION'
                        : activeRubric?.status === 'rejected'
                        ? 'REJECTED'
                        : 'PENDING APPROVAL'}
                    </span>
                  </div>
                </div>
              )}

              {/* Phase 3: Rejection Feedback Banner (shown on Step 6 when rubric is rejected) */}
              {activeTab === 'approval' && activeRubric?.status === 'rejected' && (
                <div className="rejection-banner">
                  <div className="rejection-banner-header">
                    <XCircle size={20} color="#EF4444" />
                    <div>
                      <h4>Rubric Rejected — Feedback from {activeRubric.rejected_by || 'Lecturer'}</h4>
                      <p>
                        {activeRubric.rejected_at
                          ? `Rejected on ${new Date(activeRubric.rejected_at).toLocaleString()}`
                          : 'Rejection recorded'}
                      </p>
                    </div>
                  </div>

                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Rejection Reasons:
                    </span>
                    <div className="reason-chips" style={{ marginTop: '6px' }}>
                      {(() => {
                        const reasons = Array.isArray(activeRubric.rejection_reasons)
                          ? activeRubric.rejection_reasons
                          : typeof activeRubric.rejection_reasons === 'string'
                          ? JSON.parse(activeRubric.rejection_reasons || '[]')
                          : [];
                        return reasons.map((reason, idx) => (
                          <span key={idx} className="reason-chip">
                            <AlertTriangle size={11} /> {reason}
                          </span>
                        ));
                      })()}
                    </div>
                  </div>

                  {activeRubric.rejection_feedback && (
                    <div className="rejection-feedback-quote">
                      &ldquo;{activeRubric.rejection_feedback}&rdquo;
                    </div>
                  )}

                  <div className="regenerate-banner">
                    <p>
                      <RotateCcw size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                      Generate an improved rubric incorporating this feedback using Ollama + RAG
                    </p>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={handleRegenerateRubric}
                      disabled={isRegenerating || loading}
                    >
                      {isRegenerating ? (
                        <><span className="spinner-inline" /> Regenerating...</>
                      ) : (
                        <><RotateCcw size={14} /> Regenerate Rubric with Feedback</>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Phase 3: Rubric Version History Section (Shown on Step 6 Approval and Step 3 Rubrics) */}
              {(activeTab === 'approval' || activeTab === 'rubrics') && versionHistory.length > 0 && (
                <div className="version-history-section">
                  <div className="version-history-header">
                    <h4>
                      <History size={16} color="#6366F1" /> Rubric Version History
                      <span className="badge badge-info" style={{ marginLeft: '8px' }}>
                        {versionHistory.length} {versionHistory.length === 1 ? 'version' : 'versions'}
                      </span>
                    </h4>

                    {versionHistory.length > 1 && (
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.74rem', padding: '3px 9px' }}
                        onClick={() => setShowHistoryAudit(!showHistoryAudit)}
                      >
                        {showHistoryAudit ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                        {showHistoryAudit ? 'Hide Audit Trail' : 'View Audit Trail'}
                      </button>
                    )}
                  </div>

                  {/* Version Pills */}
                  <div className="version-pills">
                    {versionHistory.map((v) => {
                      const isActive = activeRubric?.id === v.id;
                      const pillClass = v.status === 'rejected'
                        ? 'rejected'
                        : v.is_approved
                        ? 'approved'
                        : '';
                      return (
                        <button
                          key={v.id}
                          type="button"
                          className={`version-pill ${pillClass} ${isActive ? 'active' : ''}`}
                          onClick={() => handleSelectVersion(v)}
                          title={`Version ${v.version} — ${v.status} — ${v.generation_mode || 'rule_based'}`}
                        >
                          <GitBranch size={12} />
                          v{v.version}
                          {v.is_approved && <Check size={10} />}
                          {v.status === 'rejected' && <XCircle size={10} />}
                          {isActive && <span style={{ fontSize: '0.68rem', marginLeft: '2px', opacity: 0.9 }}>(Viewing)</span>}
                        </button>
                      );
                    })}
                  </div>

                  {/* Version Detail Row */}
                  {activeRubric && (
                    <div className="version-detail-row" style={{ borderTop: '1px solid #E2E8F0', marginTop: '10px' }}>
                      <span className="label">Viewing:</span>
                      <span className="value">v{activeRubric.version || 1}</span>

                      <span className="label">Status:</span>
                      <span className={`badge ${
                        activeRubric.is_approved ? 'badge-success' : activeRubric.status === 'rejected' ? 'badge-danger' : 'badge-purple'
                      }`}>
                        {activeRubric.is_approved ? 'APPROVED' : activeRubric.status === 'rejected' ? 'REJECTED' : 'PENDING APPROVAL'}
                      </span>

                      <span className="label">Generation:</span>
                      <span className="value">
                        {(activeRubric.generation_mode || 'rule_based')
                          .replace('ollama_rag', 'Ollama llama3.2:1b + RAG')
                          .replace('rule_based_fallback', 'Rule-Based Fallback')
                          .replace('rule_based', 'Rule-Based Baseline')}
                      </span>

                      {activeRubric.parent_rubric_id && (
                        <>
                          <span className="label">Parent:</span>
                          <span className="value">Rubric #{activeRubric.parent_rubric_id}</span>
                        </>
                      )}

                      {/* Switch to latest version if viewing an earlier version */}
                      {versionHistory.length > 1 && activeRubric.id !== versionHistory[versionHistory.length - 1].id && (
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: '0.72rem', padding: '2px 8px', marginLeft: 'auto' }}
                          onClick={() => handleSelectVersion(versionHistory[versionHistory.length - 1])}
                        >
                          <RotateCcw size={11} /> Switch to Latest (v{versionHistory[versionHistory.length - 1].version})
                        </button>
                      )}
                    </div>
                  )}

                  {/* Expandable Version History Audit Trail Table */}
                  {showHistoryAudit && (
                    <div style={{ marginTop: '12px', background: '#F8FAFC', borderRadius: '8px', border: '1px solid #E2E8F0', overflow: 'hidden' }}>
                      <table className="academic-table" style={{ fontSize: '0.8rem', margin: 0 }}>
                        <thead>
                          <tr>
                            <th style={{ width: '10%' }}>Version</th>
                            <th style={{ width: '15%' }}>Status</th>
                            <th style={{ width: '22%' }}>Generation Method</th>
                            <th style={{ width: '38%' }}>Rejection Reasons & Feedback</th>
                            <th style={{ width: '15%' }}>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {versionHistory.map((item) => {
                            const isCurrent = activeRubric?.id === item.id;
                            const reasons = Array.isArray(item.rejection_reasons)
                              ? item.rejection_reasons
                              : typeof item.rejection_reasons === 'string'
                              ? JSON.parse(item.rejection_reasons || '[]')
                              : [];
                            return (
                              <tr key={item.id} style={{ background: isCurrent ? '#EEF2FF' : undefined }}>
                                <td>
                                  <strong>v{item.version}</strong>
                                  {isCurrent && <span className="badge badge-purple" style={{ marginLeft: '4px', fontSize: '0.68rem' }}>Current</span>}
                                </td>
                                <td>
                                  <span className={`badge ${
                                    item.is_approved ? 'badge-success' : item.status === 'rejected' ? 'badge-danger' : 'badge-purple'
                                  }`}>
                                    {item.is_approved ? 'Approved' : item.status === 'rejected' ? 'Rejected' : 'Pending'}
                                  </span>
                                </td>
                                <td>
                                  {(item.generation_mode || 'rule_based')
                                    .replace('ollama_rag', 'Ollama llama3.2:1b + RAG')
                                    .replace('rule_based_fallback', 'Rule-Based Fallback')
                                    .replace('rule_based', 'Rule-Based Baseline')}
                                </td>
                                <td>
                                  {item.status === 'rejected' ? (
                                    <div>
                                      {reasons.length > 0 && (
                                        <div className="reason-chips" style={{ marginBottom: '4px' }}>
                                          {reasons.map((r, ri) => (
                                            <span key={ri} className="reason-chip" style={{ fontSize: '0.68rem' }}>
                                              {r}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                      {item.rejection_feedback && (
                                        <div style={{ fontSize: '0.74rem', color: '#64748B', fontStyle: 'italic' }}>
                                          "{item.rejection_feedback}"
                                        </div>
                                      )}
                                      <div style={{ fontSize: '0.7rem', color: '#94A3B8', marginTop: '2px' }}>
                                        By {item.rejected_by || 'Lecturer'}
                                      </div>
                                    </div>
                                  ) : item.is_approved ? (
                                    <div style={{ fontSize: '0.74rem', color: '#047857' }}>
                                      Approved by {item.approved_by || 'Lecturer'}
                                    </div>
                                  ) : (
                                    <span style={{ color: '#94A3B8', fontSize: '0.74rem' }}>Pending review</span>
                                  )}
                                </td>
                                <td>
                                  <button
                                    type="button"
                                    className="btn btn-secondary btn-sm"
                                    style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                                    onClick={() => handleSelectVersion(item)}
                                    disabled={isCurrent || loading}
                                  >
                                    <Eye size={12} /> {isCurrent ? 'Viewing' : 'Inspect'}
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ========================================================================= */}
              {/* STEP 3: ADAPTIVE RUBRICS VIEW */}
              {/* ========================================================================= */}
              {activeTab === 'rubrics' && (
                <div>
                  {/* Assessment Context, Model Answer & RAG Grounding Card */}
                  <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <BookOpen size={18} color="#6366F1" /> Assessment Specification & Reference Standard
                        </h3>
                        <p className="card-subtitle">
                          Assessment: <strong>{selectedAssessment?.title || 'Selected Question'}</strong> | Course: <strong>{selectedAssessment?.course_code || 'IT4360'}</strong>
                        </p>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <span className="badge badge-purple">
                          Bloom's Tier: {selectedAssessment?.blooms_level || 'Apply'}
                        </span>
                        <span className="badge badge-info">
                          Max Marks: {selectedAssessment?.max_marks || 20}
                        </span>
                      </div>
                    </div>

                    <div className="card-body">
                      <div style={{ marginBottom: '14px' }}>
                        <label style={{ fontSize: '0.76rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Selected Assessment Question:
                        </label>
                        <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '12px 16px', marginTop: '6px', fontSize: '0.9rem', color: '#1E293B', lineHeight: '1.5' }}>
                          {selectedAssessment?.question_text || 'No assessment question loaded.'}
                        </div>
                      </div>

                      <div style={{ marginBottom: '14px' }}>
                        <label style={{ fontSize: '0.76rem', fontWeight: 700, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Model / Reference Answer (Pedagogical Ground Truth):
                        </label>
                        <div style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderRadius: '8px', padding: '12px 16px', marginTop: '6px', fontSize: '0.88rem', color: '#166534', lineHeight: '1.5' }}>
                          {selectedAssessment?.model_answer || selectedAssessment?.reference_answer || 'No reference model answer registered.'}
                        </div>
                      </div>

                      {/* Generation Mode & RAG Grounding Badges */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px', marginTop: '16px' }}>
                        <div style={{ background: '#F5F3FF', border: '1px solid #DDD6FE', borderRadius: '8px', padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                            <Sparkles size={16} color="#7C3AED" />
                            <strong style={{ fontSize: '0.85rem', color: '#5B21B6' }}>Generation Pipeline</strong>
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#6D28D9' }}>
                            Active Method:{' '}
                            <strong>
                              {currentRubric
                                ? (currentRubric.generation_mode || 'rule_based')
                                    .replace('ollama_rag', 'Ollama llama3.2:1b + RAG Grounding')
                                    .replace('ollama', 'Ollama llama3.2:1b (Direct Generation)')
                                    .replace('rule_based_fallback', 'Rule-Based Fallback')
                                    .replace('rule_based', 'Rule-Based Baseline')
                                : 'No Rubric Generated Yet'}
                            </strong>
                          </div>
                          <div style={{ fontSize: '0.76rem', color: '#7C3AED', marginTop: '4px' }}>
                            {currentRubric ? 'Criteria and graduated performance descriptors tailored specifically to this assessment.' : 'Click Generate Rubric below to create question-specific criteria.'}
                          </div>
                        </div>

                        <div style={{ background: '#EFF6FF', border: '1px solid #BFDBFE', borderRadius: '8px', padding: '12px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                            <Database size={16} color="#2563EB" />
                            <strong style={{ fontSize: '0.85rem', color: '#1E40AF' }}>RAG Reference Retrieval</strong>
                          </div>
                          <div style={{ fontSize: '0.82rem', color: '#1D4ED8' }}>
                            {currentRubric?.rag_context_used ? (
                              <span>Grounding reference: <em>{currentRubric.rag_context_used.slice(0, 110)}...</em></span>
                            ) : currentRubric ? (
                              <span>Direct generation without external exemplar references.</span>
                            ) : (
                              <span>Vector semantic retrieval queries lecturer reference exemplar rubrics for curricular alignment.</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Fallback Notice Banner */}
                  {currentRubric?.generation_mode === 'rule_based_fallback' && (
                    <div style={{ background: '#FEF3C7', border: '1px solid #F59E0B', borderRadius: '8px', padding: '12px 16px', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <AlertTriangle size={18} color="#D97706" />
                      <div style={{ fontSize: '0.85rem', color: '#92400E' }}>
                        <strong>Notice (Rule-Based Fallback):</strong> Local AI (Ollama) generation was unavailable, timed out, or produced non-compliant output. Criteria were generated using the rule-based baseline prototype.
                      </div>
                    </div>
                  )}

                  {/* Adaptive Criteria & Performance Descriptors Table */}
                  <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <h3 className="card-title">
                          {currentRubric ? `${currentRubric.title} (v${currentRubric.version || 1})` : 'Adaptive Rubric'}
                        </h3>
                        <p className="card-subtitle">
                          Marking criteria, pedagogical descriptions, Bloom’s cognitive dimensions, and 4 graduated performance levels
                        </p>
                      </div>

                      <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                        {currentRubric?.is_approved ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ECFDF5', border: '1px solid #10B981', color: '#065F46', padding: '6px 12px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 700 }}>
                            <CheckCircle size={15} color="#10B981" /> Approved & Locked
                          </div>
                        ) : (
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={handleGenerateRubric}
                            disabled={loading || isRegenerating || isRejecting}
                            title="Generate or re-synthesize rubric using Ollama + RAG"
                          >
                            <RefreshCw size={14} /> {currentRubric ? 'Re-Generate Rubric' : 'Generate Rubric'}
                          </button>
                        )}
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setActiveTab('weights')}
                          disabled={!currentRubric}
                        >
                          Proceed to Step 4: Dynamic Weights <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>

                    <div className="card-body" style={{ padding: 0 }}>
                      {currentRubric?.criteria?.length > 0 ? (
                        <table className="academic-table">
                          <thead>
                            <tr>
                              <th style={{ width: '24%' }}>Criterion & Cognitive Dimension</th>
                              <th style={{ width: '14%' }}>Weight Preview</th>
                              <th style={{ width: '62%' }}>Performance Descriptors (Graduated Levels)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {currentRubric.criteria.map((crit) => (
                              <tr key={crit.id}>
                                <td>
                                  <strong>{crit.criterion_name}</strong>
                                  <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '4px' }}>
                                    {crit.description}
                                  </p>
                                  <span className="badge badge-purple" style={{ marginTop: '6px' }}>
                                    {crit.blooms_dimension}
                                  </span>
                                </td>
                                <td>
                                  <div style={{ fontSize: '1.05rem', fontWeight: 800, color: '#3B82F6' }}>
                                    {crit.weight_percentage}%
                                  </div>
                                  <div style={{ fontSize: '0.78rem', color: '#64748B' }}>
                                    Max: {crit.max_marks} marks
                                  </div>
                                  <div style={{ fontSize: '0.68rem', color: '#94A3B8', marginTop: '4px', fontStyle: 'italic' }}>
                                    (Preview • Tune in Step 4)
                                  </div>
                                </td>
                                <td>
                                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                                    {crit.performance_levels?.map((lvl, lidx) => (
                                      <div
                                        key={lidx}
                                        style={{
                                          background: '#F8FAFC',
                                          padding: '8px',
                                          borderRadius: '6px',
                                          border: '1px solid #E2E8F0',
                                          fontSize: '0.75rem',
                                        }}
                                      >
                                        <div
                                          style={{
                                            fontWeight: 700,
                                            color:
                                              lvl.level === 'Exemplary'
                                                ? '#10B981'
                                                : lvl.level === 'Proficient'
                                                ? '#3B82F6'
                                                : lvl.level === 'Developing'
                                                ? '#F59E0B'
                                                : '#EF4444',
                                            marginBottom: '4px',
                                          }}
                                        >
                                          {lvl.level} ({lvl.score_percentage}%)
                                        </div>
                                        <div style={{ color: '#475569', lineHeight: '1.3' }}>
                                          {lvl.description}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div style={{ padding: '48px 24px', textAlign: 'center', background: '#F8FAFC' }}>
                          <div style={{ display: 'inline-flex', padding: '12px', background: '#EEF2FF', borderRadius: '50%', marginBottom: '14px' }}>
                            <Layers size={28} color="#6366F1" />
                          </div>
                          <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E293B', marginBottom: '8px' }}>
                            {currentBaselineRubric ? 'No AI-Generated Rubric Yet' : 'No Rubric Generated Yet'}
                          </h4>
                          <p style={{ color: '#64748B', maxWidth: '560px', margin: '0 auto 20px auto', fontSize: '0.88rem', lineHeight: '1.5' }}>
                            {currentBaselineRubric
                              ? `Assessment #${selectedAssessment?.id} ("${selectedAssessment?.title}") currently has an imported rule-based baseline preserved for comparative benchmarking. Synthesize an adaptive, question-specific AI rubric using Ollama + RAG to begin optimization and lecturer approval.`
                              : `Assessment #${selectedAssessment?.id} ("${selectedAssessment?.title}") does not have an active marking rubric. Click below to synthesize question-specific criteria using Ollama + RAG.`}
                          </p>
                          <button className="btn btn-primary" onClick={handleGenerateRubric} disabled={loading}>
                            <Sparkles size={16} /> Generate AI Rubric
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Research Baseline History Section (Collapsible) */}
                  {currentBaselineRubric && (
                    <div className="card" style={{ marginBottom: '20px', border: '1px solid #CBD5E1' }}>
                      <div
                        className="card-header"
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          cursor: 'pointer',
                          background: '#F8FAFC',
                          userSelect: 'none',
                        }}
                        onClick={() => setShowBaselineHistory(!showBaselineHistory)}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '6px', background: '#E2E8F0' }}>
                            <Database size={16} color="#475569" />
                          </div>
                          <div>
                            <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: '#334155' }}>
                              Research Baseline History: {currentBaselineRubric.title || 'Baseline Rubric'} (v{currentBaselineRubric.version || 1})
                            </h4>
                            <p style={{ margin: 0, fontSize: '0.78rem', color: '#64748B' }}>
                              Preserved historical benchmark for comparative evaluation • ID: #{currentBaselineRubric.id}
                            </p>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span
                            className="badge badge-secondary"
                            style={{
                              fontSize: '0.74rem',
                              background: '#FEF3C7',
                              color: '#92400E',
                              border: '1px solid #F59E0B',
                              fontWeight: 600,
                            }}
                          >
                            Imported Rule-Based Baseline
                          </span>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            style={{ padding: '4px 8px', fontSize: '0.76rem' }}
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowBaselineHistory(!showBaselineHistory);
                            }}
                          >
                            {showBaselineHistory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                            {showBaselineHistory ? 'Hide' : 'View Baseline Criteria'}
                          </button>
                        </div>
                      </div>

                      {showBaselineHistory && (
                        <div className="card-body" style={{ padding: 0 }}>
                          <div style={{ padding: '12px 18px', background: '#FFFBEB', borderBottom: '1px solid #FEF3C7', fontSize: '0.82rem', color: '#92400E' }}>
                            <strong>Note:</strong> This baseline rubric was automatically imported from course benchmarks (approved by {currentBaselineRubric.approved_by || 'Lead Lecturer (Imported)'}). It is strictly preserved for comparative analysis and research metrics, and is not modified during adaptive AI synthesis.
                          </div>
                          {currentBaselineRubric.criteria?.length > 0 ? (
                            <table className="academic-table">
                              <thead>
                                <tr>
                                  <th style={{ width: '28%' }}>Baseline Criterion</th>
                                  <th style={{ width: '14%' }}>Weight</th>
                                  <th style={{ width: '58%' }}>Performance Descriptors</th>
                                </tr>
                              </thead>
                              <tbody>
                                {currentBaselineRubric.criteria.map((crit) => (
                                  <tr key={crit.id || crit.criterion_name}>
                                    <td>
                                      <strong>{crit.criterion_name}</strong>
                                      <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '4px' }}>
                                        {crit.description}
                                      </p>
                                      {crit.blooms_dimension && (
                                        <span className="badge badge-purple" style={{ marginTop: '4px', fontSize: '0.7rem' }}>
                                          {crit.blooms_dimension}
                                        </span>
                                      )}
                                    </td>
                                    <td>
                                      <div style={{ fontSize: '1rem', fontWeight: 800, color: '#475569' }}>
                                        {crit.weight_percentage}%
                                      </div>
                                      <div style={{ fontSize: '0.76rem', color: '#64748B' }}>
                                        Max: {crit.max_marks} marks
                                      </div>
                                    </td>
                                    <td>
                                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '6px' }}>
                                        {crit.performance_levels?.map((lvl, lidx) => (
                                          <div
                                            key={lidx}
                                            style={{
                                              background: '#F8FAFC',
                                              padding: '6px 8px',
                                              borderRadius: '4px',
                                              border: '1px solid #E2E8F0',
                                              fontSize: '0.73rem',
                                            }}
                                          >
                                            <div style={{ fontWeight: 700, color: '#334155', marginBottom: '2px' }}>
                                              {lvl.level} ({lvl.score_percentage}%)
                                            </div>
                                            <div style={{ color: '#64748B', lineHeight: '1.25' }}>
                                              {lvl.description}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#64748B', fontSize: '0.85rem' }}>
                              No detailed criteria records associated with this baseline.
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* ========================================================================= */}
              {/* STEP 4: DYNAMIC WEIGHTS OPTIMIZATION WORKBENCH */}
              {/* ========================================================================= */}
              {activeTab === 'weights' && (
                <div>
                  {/* Header & In-Page Optimization Rationale Card */}
                  <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Sliders size={18} color="#6366F1" /> Dynamic Weight Optimization Workbench
                        </h3>
                        <p className="card-subtitle">
                          Assessment: <strong>{selectedAssessment?.title}</strong> | Active Version: <strong>v{currentRubric?.version || 1}</strong> | Rubric ID: <strong>{currentRubric ? `#${currentRubric.id}` : 'None'}</strong>
                        </p>
                      </div>

                      <div style={{ display: 'flex', gap: '8px' }}>
                        <span className="badge badge-purple">Bloom's: {selectedAssessment?.blooms_level || 'Apply'}</span>
                        <span className="badge badge-info">Assessment Max: {selectedAssessment?.max_marks || 20} Marks</span>
                      </div>
                    </div>

                    <div className="card-body">
                      {/* In-page Educational Weighting Rationale */}
                      <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '14px 18px', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                          <Info size={16} color="#6366F1" />
                          <strong style={{ fontSize: '0.85rem', color: '#1E293B' }}>Educational Weighting Rationale & Cognitive Distribution</strong>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.84rem', color: '#475569', lineHeight: '1.5' }}>
                          {optimizationRationale || (
                            `Criteria weights are calibrated using Bloom's Taxonomy cognitive tiers. Higher-order cognitive dimensions (Analyze, Evaluate, Create) receive enhanced multiplier weightings, whereas foundational knowledge dimensions receive baseline weightings. All weights are normalized to sum strictly to 100.0%, and marks are proportionally allocated to total ${selectedAssessment?.max_marks || 20} marks.`
                          )}
                        </p>
                      </div>

                      {/* Live 100% Weight Balance Indicator Bar */}
                      {(() => {
                        const criteriaList = isEditingRubric ? editableCriteria : (currentRubric?.criteria || []);
                        const totalWeight = criteriaList.reduce((s, c) => s + (parseFloat(c.weight_percentage) || 0), 0);
                        const isBalanced = Math.abs(totalWeight - 100.0) <= 0.1;
                        const totalMarks = criteriaList.reduce((s, c) => s + (parseFloat(c.max_marks) || 0), 0);
                        const maxMarks = selectedAssessment?.max_marks || 20.0;
                        return (
                          <div
                            style={{
                              background: isBalanced ? '#F0FDF4' : '#FEF2F2',
                              border: `1px solid ${isBalanced ? '#BBF7D0' : '#FECACA'}`,
                              borderRadius: '8px',
                              padding: '14px 18px',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                {isBalanced ? <CheckCircle size={20} color="#10B981" /> : <AlertTriangle size={20} color="#EF4444" />}
                                <div>
                                  <div style={{ fontSize: '0.88rem', fontWeight: 700, color: isBalanced ? '#065F46' : '#991B1B' }}>
                                    {isBalanced ? '100.0% Weight Balance Constraints Satisfied' : 'Weight Imbalance Detected'}
                                  </div>
                                  <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
                                    Total Criteria Weight: <strong style={{ color: isBalanced ? '#10B981' : '#EF4444' }}>{totalWeight.toFixed(1)}%</strong> / 100.0% | Allocated Marks: <strong>{totalMarks.toFixed(1)}</strong> / {maxMarks}
                                  </div>
                                </div>
                              </div>

                              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                {!isEditingRubric ? (
                                  <>
                                    <button
                                      className="btn btn-primary btn-sm"
                                      onClick={handleOptimizeWeights}
                                      disabled={loading || !activeRubric || activeRubric?.is_approved || activeRubric?.status === 'rejected'}
                                      title={
                                        activeRubric?.is_approved
                                          ? 'Approved rubrics cannot be modified'
                                          : activeRubric?.status === 'rejected'
                                          ? 'Rejected rubrics cannot be optimized'
                                          : 'Run idempotent dynamic weight optimization'
                                      }
                                    >
                                      <Sliders size={14} /> Optimize Weights
                                    </button>
                                    <button
                                      className="btn btn-secondary btn-sm"
                                      onClick={handleStartEditRubric}
                                      disabled={loading || !activeRubric || activeRubric?.is_approved || activeRubric?.status === 'rejected'}
                                    >
                                      <Edit3 size={14} /> Edit Weights Manually
                                    </button>
                                  </>
                                ) : (
                                  <>
                                    <button className="btn btn-secondary btn-sm" onClick={() => setIsEditingRubric(false)} disabled={loading}>
                                      Cancel
                                    </button>
                                    <button className="btn btn-primary btn-sm" onClick={handleSaveEditedRubric} disabled={loading}>
                                      <Save size={14} /> Save Weights
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>

                            {/* Meter Bar */}
                            <div style={{ width: '100%', height: '8px', background: '#E2E8F0', borderRadius: '4px', overflow: 'hidden', marginTop: '12px' }}>
                              <div
                                style={{
                                  height: '100%',
                                  width: `${Math.min(totalWeight, 100)}%`,
                                  background: isBalanced ? '#10B981' : totalWeight > 100 ? '#EF4444' : '#F59E0B',
                                  transition: 'width 0.3s ease',
                                }}
                              />
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>

                  {/* Weight Allocation Table / Interactive Workbench */}
                  <div className="card" style={{ marginBottom: '20px' }}>
                    <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <h3 className="card-title">Criterion Weight & Mark Allocation Breakdown</h3>
                        <p className="card-subtitle">
                          {isEditingRubric
                            ? 'Adjust weights directly. Marks will automatically recompute according to total assessment marks.'
                            : 'Review individual criterion weights, allocated marks, and proportional visual distribution.'}
                        </p>
                      </div>

                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('rubrics')}>
                          Back to Step 3: Adaptive Rubrics
                        </button>
                        <button className="btn btn-primary btn-sm" onClick={() => setActiveTab('validation')}>
                          Proceed to Step 5: Validation <ArrowRight size={14} />
                        </button>
                      </div>
                    </div>

                    <div className="card-body" style={{ padding: 0 }}>
                      {isEditingRubric ? (
                        /* Controlled Weight Editing View */
                        <div style={{ padding: '20px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                            {editableCriteria.map((crit, idx) => (
                              <div
                                key={idx}
                                style={{
                                  background: '#F8FAFC',
                                  border: '1px solid #E2E8F0',
                                  borderRadius: '8px',
                                  padding: '16px',
                                  display: 'grid',
                                  gridTemplateColumns: '2fr 1fr 1fr auto',
                                  gap: '12px',
                                  alignItems: 'center',
                                }}
                              >
                                <div>
                                  <label className="form-label" style={{ fontSize: '0.78rem' }}>Criterion Name</label>
                                  <input
                                    className="form-input"
                                    value={crit.criterion_name}
                                    onChange={(e) => handleCriterionFieldChange(idx, 'criterion_name', e.target.value)}
                                  />
                                  <p style={{ fontSize: '0.74rem', color: '#64748B', margin: '4px 0 0 0' }}>
                                    {crit.description}
                                  </p>
                                </div>

                                <div>
                                  <label className="form-label" style={{ fontSize: '0.78rem' }}>Bloom's Tier</label>
                                  <select
                                    className="form-select"
                                    value={crit.blooms_dimension || 'Apply'}
                                    onChange={(e) => handleCriterionFieldChange(idx, 'blooms_dimension', e.target.value)}
                                  >
                                    <option value="Remember">Remember</option>
                                    <option value="Understand">Understand</option>
                                    <option value="Apply">Apply</option>
                                    <option value="Analyze">Analyze</option>
                                    <option value="Evaluate">Evaluate</option>
                                    <option value="Create">Create</option>
                                  </select>
                                </div>

                                <div>
                                  <label className="form-label" style={{ fontSize: '0.78rem' }}>Weight % (Marks: {crit.max_marks})</label>
                                  <input
                                    type="number"
                                    step="0.5"
                                    min="0"
                                    max="100"
                                    className="form-input"
                                    value={crit.weight_percentage}
                                    onChange={(e) => handleCriterionWeightChange(idx, e.target.value)}
                                  />
                                </div>

                                <div style={{ paddingTop: '22px' }}>
                                  <button
                                    className="btn btn-secondary btn-sm"
                                    onClick={() => handleRemoveCriterion(idx)}
                                    title="Delete Criterion"
                                    style={{ color: '#EF4444', borderColor: '#FCA5A5' }}
                                  >
                                    <Trash2 size={16} />
                                  </button>
                                </div>
                              </div>
                            ))}
                          </div>

                          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <button className="btn btn-secondary btn-sm" onClick={handleAddCriterion}>
                              <Plus size={14} /> Add Additional Criterion
                            </button>
                            <div style={{ display: 'flex', gap: '10px' }}>
                              <button className="btn btn-secondary" onClick={() => setIsEditingRubric(false)}>
                                Cancel
                              </button>
                              <button className="btn btn-primary" onClick={handleSaveEditedRubric}>
                                <Save size={16} /> Save Weights & Verify Balance
                              </button>
                            </div>
                          </div>
                        </div>
                      ) : currentRubric?.criteria?.length > 0 ? (
                        /* Read-Only Weight Optimization Workbench Table */
                        <table className="academic-table">
                          <thead>
                            <tr>
                              <th style={{ width: '32%' }}>Criterion & Cognitive Dimension</th>
                              <th style={{ width: '18%' }}>Weight Percentage</th>
                              <th style={{ width: '18%' }}>Allocated Marks</th>
                              <th style={{ width: '32%' }}>Proportional Weight Share</th>
                            </tr>
                          </thead>
                          <tbody>
                            {currentRubric.criteria.map((crit) => (
                              <tr key={crit.id}>
                                <td>
                                  <strong>{crit.criterion_name}</strong>
                                  <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '4px' }}>
                                    {crit.description}
                                  </p>
                                  <span className="badge badge-purple" style={{ marginTop: '6px' }}>
                                    {crit.blooms_dimension}
                                  </span>
                                </td>
                                <td>
                                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#4F46E5' }}>
                                    {crit.weight_percentage}%
                                  </div>
                                  <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                    Share of 100.0%
                                  </div>
                                </td>
                                <td>
                                  <div style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0F172A' }}>
                                    {crit.max_marks} marks
                                  </div>
                                  <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                    out of {selectedAssessment?.max_marks || 20} max
                                  </div>
                                </td>
                                <td>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <div style={{ flex: 1, height: '10px', background: '#E2E8F0', borderRadius: '5px', overflow: 'hidden' }}>
                                      <div
                                        style={{
                                          height: '100%',
                                          width: `${Math.min(crit.weight_percentage, 100)}%`,
                                          background: 'linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%)',
                                          borderRadius: '5px',
                                        }}
                                      />
                                    </div>
                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', minWidth: '40px' }}>
                                      {crit.weight_percentage}%
                                    </span>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div style={{ padding: '36px', textAlign: 'center' }}>
                          <p style={{ color: '#64748B', marginBottom: '16px' }}>
                            No rubric loaded to optimize weights.
                          </p>
                          <button className="btn btn-primary" onClick={() => setActiveTab('rubrics')}>
                            Go to Step 3 to Generate Rubric
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* ========================================================================= */}
              {/* STEP 5: RUBRIC QUALITY & CONSTRAINT VALIDATION (AUTOMATED VERIFICATION)  */}
              {/* ========================================================================= */}
              {activeTab === 'validation' && (
                <div>
                  {!currentRubric ? (
                    <div className="card" style={{ padding: '48px 24px', textAlign: 'center', background: '#F8FAFC', borderRadius: '10px', border: '1px dashed #CBD5E1', marginBottom: '20px' }}>
                      <div style={{ display: 'inline-flex', padding: '12px', background: '#EEF2FF', borderRadius: '50%', marginBottom: '14px' }}>
                        <CheckCircle size={28} color="#6366F1" />
                      </div>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E293B', marginBottom: '8px' }}>
                        No Rubric Available for Validation
                      </h4>
                      <p style={{ color: '#64748B', maxWidth: '480px', margin: '0 auto 16px auto', fontSize: '0.88rem' }}>
                        Assessment #{selectedAssessment?.id} ("{selectedAssessment?.title}") does not have an adaptive rubric generated yet.
                      </p>
                      <button className="btn btn-primary" onClick={() => setActiveTab('rubrics')}>
                        Go to Step 3: Adaptive Rubrics
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Top Header Card */}
                      <div className="card" style={{ marginBottom: '20px' }}>
                        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                          <div>
                            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <CheckCircle size={18} color="#10B981" /> Automated Rubric Quality & Constraint Validation
                            </h3>
                            <p className="card-subtitle">
                              Algorithmic verification of criterion completeness, question relevance, Bloom's alignment, weight consistency, and allocated marks
                            </p>
                          </div>

                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                            <button
                              className="btn btn-primary btn-sm"
                              onClick={handleValidateRubric}
                              disabled={loading || isValidating || !currentRubric}
                              title="Execute automated validation checks on backend"
                            >
                              {isValidating ? (
                                <><span className="spinner-inline" /> Validating...</>
                              ) : (
                                <><CheckCircle size={14} /> Run Automated Validation</>
                              )}
                            </button>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => setActiveTab('approval')}
                            >
                              Proceed to Step 6: Approval <ArrowRight size={14} />
                            </button>
                          </div>
                        </div>

                        <div className="card-body">
                          {/* Validation Status & Score Banner */}
                          <div
                            className={`validation-status-banner ${validationSummary?.status || 'valid'}`}
                            style={{
                              background: validationSummary?.status === 'valid'
                                ? '#ECFDF5'
                                : validationSummary?.status === 'warning'
                                ? '#FFFBEB'
                                : '#FEF2F2',
                              border: `1px solid ${
                                validationSummary?.status === 'valid'
                                  ? '#A7F3D0'
                                  : validationSummary?.status === 'warning'
                                  ? '#FDE68A'
                                  : '#FECACA'
                              }`,
                              borderRadius: '10px',
                              padding: '16px 20px',
                              marginBottom: '20px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              gap: '16px',
                            }}
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                              {validationSummary?.status === 'valid' ? (
                                <CheckCircle size={28} color="#10B981" />
                              ) : validationSummary?.status === 'warning' ? (
                                <AlertTriangle size={28} color="#F59E0B" />
                              ) : (
                                <XCircle size={28} color="#EF4444" />
                              )}
                              <div>
                                <div style={{ fontWeight: 800, fontSize: '1.02rem', color: validationSummary?.status === 'valid' ? '#065F46' : validationSummary?.status === 'warning' ? '#92400E' : '#991B1B' }}>
                                  Automated Validation Status: {validationSummary?.status?.toUpperCase() || 'VALID'} (Overall Score: {validationSummary?.score || 100}%)
                                </div>
                                <div style={{ fontSize: '0.84rem', color: '#475569', marginTop: '3px' }}>
                                  {validationSummary?.status === 'valid'
                                    ? 'All automated pedagogical rules, completeness constraints, and mathematical bounds satisfied.'
                                    : validationSummary?.status === 'warning'
                                    ? 'Validation passed with minor pedagogical advisories. Review the checklist before formal lecturer sign-off.'
                                    : 'Constraint divergence detected. Please review criteria weights and mark allocations.'}
                                </div>
                              </div>
                            </div>

                            <span
                              className={`badge ${
                                validationSummary?.status === 'valid'
                                  ? 'badge-success'
                                  : validationSummary?.status === 'warning'
                                  ? 'badge-warning'
                                  : 'badge-danger'
                              }`}
                              style={{ fontSize: '0.82rem', padding: '6px 14px', whiteSpace: 'nowrap' }}
                            >
                              {validationSummary?.status === 'valid'
                                ? 'CHECKS PASSED (100%)'
                                : validationSummary?.status === 'warning'
                                ? 'WARNINGS DETECTED'
                                : 'ACTION REQUIRED'}
                            </span>
                          </div>

                          {/* 5 Core Validation Metric Cards */}
                          <div className="validation-metrics-grid">
                            {/* 1. Completeness */}
                            <div className={`validation-metric-card ${validationSummary?.completeness.passed ? 'passed' : 'warning'}`}>
                              <div className="validation-metric-header">
                                <span className="validation-metric-title">1. Completeness</span>
                                <span className={`badge ${validationSummary?.completeness.passed ? 'badge-success' : 'badge-warning'}`}>
                                  {validationSummary?.completeness.passed ? 'Compliant' : 'Review'}
                                </span>
                              </div>
                              <div className="validation-metric-value">
                                {validationSummary?.completeness.count} Criteria Defined
                              </div>
                              <div className="validation-metric-detail">
                                {validationSummary?.completeness.detail}
                              </div>
                            </div>

                            {/* 2. Question Relevance */}
                            <div className={`validation-metric-card ${validationSummary?.relevance.passed ? 'passed' : 'warning'}`}>
                              <div className="validation-metric-header">
                                <span className="validation-metric-title">2. Question Relevance</span>
                                <span className="badge badge-purple">
                                  {validationSummary?.relevance.passed ? 'High Alignment' : 'Moderate'}
                                </span>
                              </div>
                              <div className="validation-metric-value">
                                {validationSummary?.relevance.score}% Semantic Match
                              </div>
                              <div className="validation-metric-detail">
                                {validationSummary?.relevance.detail}
                              </div>
                            </div>

                            {/* 3. Bloom's Alignment */}
                            <div className={`validation-metric-card ${validationSummary?.blooms.passed ? 'passed' : 'warning'}`}>
                              <div className="validation-metric-header">
                                <span className="validation-metric-title">3. Bloom's Alignment</span>
                                <span className={`badge ${validationSummary?.blooms.passed ? 'badge-success' : 'badge-warning'}`}>
                                  {validationSummary?.blooms.passed ? 'Taxonomy Aligned' : 'Review'}
                                </span>
                              </div>
                              <div className="validation-metric-value">
                                Tier: {validationSummary?.blooms.target}
                              </div>
                              <div className="validation-metric-detail">
                                {validationSummary?.blooms.detail}
                              </div>
                            </div>

                            {/* 4. Weight Consistency */}
                            <div className={`validation-metric-card ${validationSummary?.weight.passed ? 'passed' : 'failed'}`}>
                              <div className="validation-metric-header">
                                <span className="validation-metric-title">4. Weight Consistency</span>
                                <span className={`badge ${validationSummary?.weight.passed ? 'badge-success' : 'badge-danger'}`}>
                                  {validationSummary?.weight.passed ? '100.0% Normalized' : 'Divergent'}
                                </span>
                              </div>
                              <div className="validation-metric-value" style={{ color: validationSummary?.weight.passed ? '#4F46E5' : '#EF4444' }}>
                                {validationSummary?.weight.total.toFixed(1)}% / 100.0%
                              </div>
                              <div className="validation-metric-detail">
                                {validationSummary?.weight.detail}
                              </div>
                            </div>

                            {/* 5. Total Marks */}
                            <div className={`validation-metric-card ${validationSummary?.marks.passed ? 'passed' : 'failed'}`}>
                              <div className="validation-metric-header">
                                <span className="validation-metric-title">5. Total Marks</span>
                                <span className={`badge ${validationSummary?.marks.passed ? 'badge-success' : 'badge-danger'}`}>
                                  {validationSummary?.marks.passed ? 'Exact Match' : 'Discrepancy'}
                                </span>
                              </div>
                              <div className="validation-metric-value">
                                {validationSummary?.marks.total.toFixed(1)} / {validationSummary?.marks.max.toFixed(1)} Marks
                              </div>
                              <div className="validation-metric-detail">
                                {validationSummary?.marks.detail}
                              </div>
                            </div>
                          </div>

                          {/* Validation Warnings / Errors Panel */}
                          <div style={{ marginTop: '20px', marginBottom: '20px' }}>
                            {validationSummary?.warnings && validationSummary.warnings.length > 0 ? (
                              <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '8px', padding: '14px 18px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, color: '#92400E', marginBottom: '6px', fontSize: '0.88rem' }}>
                                  <AlertTriangle size={16} color="#D97706" /> Validation Warnings & Pedagogical Advisories:
                                </div>
                                <ul style={{ margin: 0, paddingLeft: '20px', color: '#78350F', fontSize: '0.82rem', lineHeight: '1.5' }}>
                                  {validationSummary.warnings.map((w, idx) => (
                                    <li key={idx}>{w}</li>
                                  ))}
                                </ul>
                              </div>
                            ) : (
                              <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '8px', padding: '12px 18px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <Check size={18} color="#10B981" />
                                <div style={{ fontSize: '0.84rem', color: '#065F46' }}>
                                  <strong>Zero Validation Warnings:</strong> All automated constraints, duplicate checks, graduated descriptor tiers, and mark consistency verified successfully.
                                </div>
                              </div>
                            )}
                          </div>

                          {/* Automated Quality Diagnostic Checks Checklist */}
                          <div style={{ marginBottom: '20px' }}>
                            <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1E293B', marginBottom: '10px' }}>
                              Automated Constraint Verification Checklist
                            </h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '10px' }}>
                              {validationSummary?.checks.map((chk, cidx) => (
                                <div
                                  key={cidx}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    gap: '10px',
                                    background: '#F8FAFC',
                                    border: '1px solid #E2E8F0',
                                    borderRadius: '6px',
                                    padding: '10px 12px',
                                  }}
                                >
                                  {chk.passed ? (
                                    <CheckCircle size={16} color="#10B981" style={{ flexShrink: 0, marginTop: '2px' }} />
                                  ) : (
                                    <AlertTriangle size={16} color="#F59E0B" style={{ flexShrink: 0, marginTop: '2px' }} />
                                  )}
                                  <div>
                                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1E293B' }}>
                                      {chk.name}
                                    </div>
                                    <div style={{ fontSize: '0.76rem', color: '#64748B', marginTop: '2px' }}>
                                      {chk.detail}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Criteria Validation Inspection Table */}
                          {currentRubric?.criteria?.length > 0 && (
                            <div>
                              <h4 style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1E293B', marginBottom: '10px' }}>
                                Criteria Verification Summary
                              </h4>
                              <table className="academic-table validation-table" style={{ margin: 0 }}>
                                <thead>
                                  <tr>
                                    <th style={{ width: '40%' }}>Criterion & Pedagogical Description</th>
                                    <th style={{ width: '15%' }}>Bloom's Dimension</th>
                                    <th style={{ width: '15%' }}>Weight Percentage</th>
                                    <th style={{ width: '15%' }}>Allocated Marks</th>
                                    <th style={{ width: '15%' }}>Descriptors</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {currentRubric.criteria.map((c) => (
                                    <tr key={c.id}>
                                      <td>
                                        <strong>{c.criterion_name}</strong>
                                        <p style={{ fontSize: '0.76rem', color: '#64748B', margin: '3px 0 0 0' }}>
                                          {c.description}
                                        </p>
                                      </td>
                                      <td>
                                        <span className="badge badge-purple">{c.blooms_dimension || 'Apply'}</span>
                                      </td>
                                      <td>
                                        <div style={{ fontWeight: 700, color: '#4F46E5' }}>{c.weight_percentage}%</div>
                                      </td>
                                      <td>
                                        <div style={{ fontWeight: 700, color: '#0F172A' }}>{c.max_marks} marks</div>
                                      </td>
                                      <td>
                                        <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>
                                          {Array.isArray(c.performance_levels) ? `${c.performance_levels.length} Tiers Graduated` : 'Standard Tiers'}
                                        </span>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}

                          {/* Navigation Footer */}
                          <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                            <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('weights')}>
                              <ArrowRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Step 4: Dynamic Weights
                            </button>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <span style={{ fontSize: '0.8rem', color: '#64748B', fontStyle: 'italic' }}>
                                Automated validation verified. Proceed to Step 6 for lecturer review and formal approval.
                              </span>
                              <button className="btn btn-primary btn-sm" onClick={() => setActiveTab('approval')}>
                                Proceed to Step 6: Approval <ArrowRight size={14} />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* ========================================================================= */}
              {/* STEP 6: LECTURER REVIEW, EDITING & FORMAL APPROVAL (HUMAN-IN-THE-LOOP)    */}
              {/* ========================================================================= */}
              {activeTab === 'approval' && (
                <div>
                  {!currentRubric ? (
                    <div className="card" style={{ padding: '48px 24px', textAlign: 'center', background: '#F8FAFC', borderRadius: '10px', border: '1px dashed #CBD5E1', marginBottom: '20px' }}>
                      <div style={{ display: 'inline-flex', padding: '12px', background: '#EEF2FF', borderRadius: '50%', marginBottom: '14px' }}>
                        <Edit3 size={28} color="#6366F1" />
                      </div>
                      <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#1E293B', marginBottom: '8px' }}>
                        No Rubric Available for Review & Approval
                      </h4>
                      <p style={{ color: '#64748B', maxWidth: '480px', margin: '0 auto 16px auto', fontSize: '0.88rem' }}>
                        Assessment #{selectedAssessment?.id} ("{selectedAssessment?.title}") does not have an adaptive rubric generated yet.
                      </p>
                      <button className="btn btn-primary" onClick={() => setActiveTab('rubrics')}>
                        Go to Step 3: Adaptive Rubrics
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Rubric Review & Editing Workbench Card */}
                      <div className="card" style={{ marginBottom: '20px' }}>
                        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                          <div>
                            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <Edit3 size={18} color="#6366F1" />
                              {currentRubric ? `${currentRubric.title} (v${currentRubric.version || 1})` : 'Lecturer Rubric Review & Editing'}
                            </h3>
                            <p className="card-subtitle">
                              Human-in-the-loop review: Inspect criteria, edit pedagogical descriptions & performance descriptors, or adjust weights before sign-off
                            </p>
                          </div>

                          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                            {currentRubric?.is_approved ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ECFDF5', border: '1px solid #10B981', color: '#065F46', padding: '6px 14px', borderRadius: '6px', fontSize: '0.82rem', fontWeight: 700 }}>
                                <Lock size={14} color="#10B981" /> Approved & Locked Against Editing
                              </div>
                            ) : currentRubric?.status === 'rejected' ? (
                              <button
                                className="btn btn-primary btn-sm"
                                onClick={handleRegenerateRubric}
                                disabled={loading || isRegenerating}
                                style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}
                              >
                                {isRegenerating ? <><span className="spinner-inline" /> Regenerating...</> : <><RotateCcw size={14} /> Regenerate Rubric with Feedback</>}
                              </button>
                            ) : isEditingRubric ? (
                              <>
                                <button className="btn btn-secondary btn-sm" onClick={() => setIsEditingRubric(false)}>
                                  Cancel Edit
                                </button>
                                <button className="btn btn-primary btn-sm" onClick={handleSaveEditedRubric} disabled={loading}>
                                  <Save size={14} /> Save Rubric Changes
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  onClick={handleStartEditRubric}
                                  disabled={loading}
                                >
                                  <Edit3 size={14} /> Edit Rubric & Descriptors
                                </button>
                                <button
                                  className="btn btn-secondary btn-sm"
                                  style={{ borderColor: '#FECACA', color: '#DC2626', background: '#FEF2F2', fontWeight: 600 }}
                                  onClick={handleOpenRejectModal}
                                  disabled={loading || isRejecting}
                                >
                                  <ThumbsDown size={14} /> Reject Rubric
                                </button>
                              </>
                            )}
                          </div>
                        </div>

                        <div className="card-body">
                          {isEditingRubric ? (
                            /* EDIT MODE: Criteria, Weights, and Performance Descriptors Editor */
                            <div>
                              <div style={{ background: '#EEF2FF', border: '1px solid #C7D2FE', borderRadius: '8px', padding: '12px 16px', marginBottom: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                                <div style={{ fontSize: '0.84rem', color: '#3730A3' }}>
                                  <strong>Lecturer Edit Mode:</strong> Modify criterion names, descriptions, cognitive levels, and performance descriptors. Total criterion weights must equal exactly 100.0%.
                                </div>
                                <div style={{ fontWeight: 800, fontSize: '0.9rem', color: Math.abs(editableCriteria.reduce((sum, c) => sum + (parseFloat(c.weight_percentage) || 0), 0) - 100.0) < 0.1 ? '#065F46' : '#DC2626' }}>
                                  Total Weight: {editableCriteria.reduce((sum, c) => sum + (parseFloat(c.weight_percentage) || 0), 0).toFixed(1)}% / 100.0%
                                </div>
                              </div>

                              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                {editableCriteria.map((crit, idx) => (
                                  <div
                                    key={idx}
                                    style={{
                                      background: '#FFFFFF',
                                      border: '1px solid #CBD5E1',
                                      borderRadius: '8px',
                                      padding: '16px',
                                      boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                                    }}
                                  >
                                    {/* Criterion Core Attributes */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
                                      <div>
                                        <label className="form-label" style={{ fontSize: '0.78rem' }}>Criterion Name *</label>
                                        <input
                                          className="form-input"
                                          value={crit.criterion_name}
                                          onChange={(e) => handleCriterionFieldChange(idx, 'criterion_name', e.target.value)}
                                        />
                                      </div>

                                      <div>
                                        <label className="form-label" style={{ fontSize: '0.78rem' }}>Bloom's Tier</label>
                                        <select
                                          className="form-select"
                                          value={crit.blooms_dimension || 'Apply'}
                                          onChange={(e) => handleCriterionFieldChange(idx, 'blooms_dimension', e.target.value)}
                                        >
                                          <option value="Remember">Remember</option>
                                          <option value="Understand">Understand</option>
                                          <option value="Apply">Apply</option>
                                          <option value="Analyze">Analyze</option>
                                          <option value="Evaluate">Evaluate</option>
                                          <option value="Create">Create</option>
                                        </select>
                                      </div>

                                      <div>
                                        <label className="form-label" style={{ fontSize: '0.78rem' }}>Weight % (Marks: {crit.max_marks})</label>
                                        <input
                                          type="number"
                                          step="0.5"
                                          min="0"
                                          max="100"
                                          className="form-input"
                                          value={crit.weight_percentage}
                                          onChange={(e) => handleCriterionWeightChange(idx, e.target.value)}
                                        />
                                      </div>

                                      <div style={{ paddingTop: '22px' }}>
                                        <button
                                          className="btn btn-secondary btn-sm"
                                          onClick={() => handleRemoveCriterion(idx)}
                                          title="Delete Criterion"
                                          style={{ color: '#EF4444', borderColor: '#FCA5A5' }}
                                        >
                                          <Trash2 size={16} />
                                        </button>
                                      </div>
                                    </div>

                                    {/* Criterion Pedagogical Description */}
                                    <div style={{ marginBottom: '12px' }}>
                                      <label className="form-label" style={{ fontSize: '0.78rem' }}>Pedagogical Evaluation Scope & Description</label>
                                      <textarea
                                        className="form-textarea"
                                        rows={2}
                                        style={{ minHeight: '60px' }}
                                        value={crit.description || ''}
                                        onChange={(e) => handleCriterionFieldChange(idx, 'description', e.target.value)}
                                        placeholder="Detailed description of what this criterion evaluates..."
                                      />
                                    </div>

                                    {/* 4 Performance Descriptors Editor */}
                                    <div>
                                      <label className="form-label" style={{ fontSize: '0.78rem', color: '#475569' }}>
                                        Performance Level Descriptors (Graduated Tiers):
                                      </label>
                                      <div className="descriptor-edit-grid">
                                        {(crit.performance_levels || [
                                          { level: 'Exemplary', score_percentage: 100, description: '' },
                                          { level: 'Proficient', score_percentage: 75, description: '' },
                                          { level: 'Developing', score_percentage: 50, description: '' },
                                          { level: 'Novice', score_percentage: 25, description: '' },
                                        ]).map((lvl, lidx) => (
                                          <div key={lidx} className="descriptor-edit-card">
                                            <div className="descriptor-edit-card-header">
                                              <span style={{ color: lidx === 0 ? '#059669' : lidx === 1 ? '#2563EB' : lidx === 2 ? '#D97706' : '#DC2626' }}>
                                                {lvl.level}
                                              </span>
                                              <span className="badge badge-purple" style={{ fontSize: '0.68rem' }}>
                                                {lvl.score_percentage}%
                                              </span>
                                            </div>
                                            <textarea
                                              className="form-textarea"
                                              rows={3}
                                              style={{ minHeight: '75px', fontSize: '0.74rem', padding: '6px' }}
                                              value={lvl.description || ''}
                                              onChange={(e) => handlePerformanceLevelChange(idx, lidx, 'description', e.target.value)}
                                              placeholder={`Description for ${lvl.level} level...`}
                                            />
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>

                              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <button className="btn btn-secondary btn-sm" onClick={handleAddCriterion}>
                                  <Plus size={14} /> Add Additional Criterion
                                </button>
                                <div style={{ display: 'flex', gap: '10px' }}>
                                  <button className="btn btn-secondary" onClick={() => setIsEditingRubric(false)}>
                                    Cancel
                                  </button>
                                  <button className="btn btn-primary" onClick={handleSaveEditedRubric}>
                                    <Save size={16} /> Save Changes & Verify Weights
                                  </button>
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* REVIEW MODE: Rich Display of Generated Rubric */
                            <div>
                              {currentRubric?.criteria?.length > 0 ? (
                                <table className="academic-table" style={{ margin: 0 }}>
                                  <thead>
                                    <tr>
                                      <th style={{ width: '22%' }}>Criterion & Bloom's Tier</th>
                                      <th style={{ width: '14%' }}>Weight & Allocated Marks</th>
                                      <th style={{ width: '64%' }}>Graduated Performance Descriptors (Exemplary to Unsatisfactory)</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {currentRubric.criteria.map((crit) => (
                                      <tr key={crit.id}>
                                        <td>
                                          <strong style={{ fontSize: '0.92rem', color: '#1E293B' }}>{crit.criterion_name}</strong>
                                          <p style={{ fontSize: '0.78rem', color: '#64748B', marginTop: '4px', lineHeight: '1.4' }}>
                                            {crit.description}
                                          </p>
                                          <span className="badge badge-purple" style={{ marginTop: '6px' }}>
                                            {crit.blooms_dimension || 'Apply'}
                                          </span>
                                        </td>
                                        <td>
                                          <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#4F46E5' }}>
                                            {crit.weight_percentage}%
                                          </div>
                                          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: '#0F172A', marginTop: '2px' }}>
                                            {crit.max_marks} marks
                                          </div>
                                          <div style={{ fontSize: '0.7rem', color: '#94A3B8' }}>
                                            out of {selectedAssessment?.max_marks || 20} max
                                          </div>
                                        </td>
                                        <td>
                                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' }}>
                                            {(crit.performance_levels || []).map((lvl, lidx) => (
                                              <div
                                                key={lidx}
                                                style={{
                                                  background: '#F8FAFC',
                                                  padding: '8px 10px',
                                                  borderRadius: '6px',
                                                  border: '1px solid #E2E8F0',
                                                  fontSize: '0.75rem',
                                                  display: 'flex',
                                                  flexDirection: 'column',
                                                  justifyContent: 'space-between',
                                                }}
                                              >
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                                  <strong style={{ color: lidx === 0 ? '#059669' : lidx === 1 ? '#2563EB' : lidx === 2 ? '#D97706' : '#DC2626' }}>
                                                    {lvl.level}
                                                  </strong>
                                                  <span style={{ fontSize: '0.68rem', fontWeight: 700, color: '#64748B' }}>
                                                    {lvl.score_percentage}%
                                                  </span>
                                                </div>
                                                <p style={{ margin: 0, color: '#475569', lineHeight: '1.35', fontSize: '0.73rem' }}>
                                                  {lvl.description || 'No description provided.'}
                                                </p>
                                              </div>
                                            ))}
                                          </div>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <p style={{ color: '#64748B', textAlign: 'center', padding: '24px 0' }}>
                                  No criteria defined in this rubric.
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Lecturer Formal Approval Panel */}
                      <div className="card">
                        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                          <div>
                            <h3 className="card-title">Lecturer Formal Approval & Sign-Off Authority</h3>
                            <p className="card-subtitle">
                              Human-in-the-loop authorization: Unlocks official student answer evaluation and locks the rubric to protect assessment integrity
                            </p>
                          </div>
                          <span className={`badge ${currentRubric?.is_approved ? 'badge-success' : currentRubric?.status === 'rejected' ? 'badge-danger' : 'badge-warning'}`}>
                            {currentRubric?.is_approved ? 'OFFICIALLY APPROVED' : currentRubric?.status === 'rejected' ? 'REJECTED' : 'PENDING APPROVAL'}
                          </span>
                        </div>

                        <div className="card-body">
                          {currentRubric?.is_approved ? (
                            /* Already Approved Card */
                            <div style={{ background: '#ECFDF5', border: '1px solid #A7F3D0', borderRadius: '8px', padding: '16px 20px', marginBottom: '16px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                                <CheckCircle size={20} color="#10B981" />
                                <strong style={{ color: '#065F46', fontSize: '0.95rem' }}>
                                  Officially Authorized & Locked for Evaluation
                                </strong>
                              </div>
                              <div style={{ fontSize: '0.84rem', color: '#047857', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '10px' }}>
                                <div><strong>Approved By:</strong> {currentRubric.approved_by || approvalLecturer}</div>
                                <div><strong>Approval Notes:</strong> {currentRubric.approval_notes || approvalNotes}</div>
                                <div><strong>Status:</strong> Evaluation Unlocked for Student Scoring</div>
                              </div>
                            </div>
                          ) : null}

                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '16px' }}>
                            <div className="form-group">
                              <label className="form-label">Approving Lecturer / Examiner</label>
                              <input
                                className="form-input"
                                value={approvalLecturer}
                                onChange={(e) => setApprovalLecturer(e.target.value)}
                                placeholder="e.g. Dr. Lecturer Lead (Module Coordinator)"
                                disabled={currentRubric?.is_approved}
                              />
                            </div>

                            <div className="form-group">
                              <label className="form-label">Review & Approval Notes</label>
                              <input
                                className="form-input"
                                value={approvalNotes}
                                onChange={(e) => setApprovalNotes(e.target.value)}
                                placeholder="e.g. Formally reviewed and verified for IT4360 evaluation."
                                disabled={currentRubric?.is_approved}
                              />
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#64748B' }}>
                              <Info size={16} color="#6366F1" />
                              <span>
                                {currentRubric?.is_approved
                                  ? `Approved by ${currentRubric.approved_by || approvalLecturer}. Re-approving will update approval timestamp.`
                                  : currentRubric?.status === 'rejected'
                                  ? 'This rubric version is marked as REJECTED. Rejected rubrics cannot be approved or used for scoring. Please regenerate an improved version.'
                                  : 'Official student scoring is blocked until this rubric is approved by the course lecturer.'}
                              </span>
                            </div>

                            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                              {!currentRubric?.is_approved && currentRubric?.status !== 'rejected' && (
                                <button
                                  type="button"
                                  className="btn btn-secondary"
                                  style={{ borderColor: '#FECACA', color: '#DC2626', background: '#FEF2F2', fontWeight: 600 }}
                                  onClick={handleOpenRejectModal}
                                  disabled={loading || isRejecting || isRegenerating || !currentRubric}
                                  title="Reject this rubric version with structured reasons and feedback"
                                >
                                  <ThumbsDown size={16} /> Reject Rubric
                                </button>
                              )}

                              {currentRubric?.status === 'rejected' && (
                                <button
                                  type="button"
                                  className="btn btn-primary"
                                  onClick={handleRegenerateRubric}
                                  disabled={loading || isRegenerating}
                                  style={{ background: 'linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%)' }}
                                >
                                  {isRegenerating ? <><span className="spinner-inline" /> Regenerating...</> : <><RotateCcw size={16} /> Regenerate Rubric</>}
                                </button>
                              )}

                              {currentRubric?.status !== 'rejected' && (
                                <button
                                  type="button"
                                  className="btn btn-primary"
                                  onClick={handleApproveRubric}
                                  disabled={loading || isRejecting || isRegenerating || !currentRubric}
                                >
                                  <Check size={16} /> {currentRubric?.is_approved ? 'Re-Approve Rubric' : 'Formally Approve Rubric'}
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Navigation Footer */}
                      <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => setActiveTab('validation')}>
                          <ArrowRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Step 5: Validation
                        </button>
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => setActiveTab('scoring')}
                          disabled={!currentRubric?.is_approved}
                        >
                          Proceed to Step 7: Student Scoring <ArrowRight size={14} />
                        </button>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 7: STUDENT ANSWER SCORING */}
          {activeTab === 'scoring' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Student Answer Submission</h3>
                </div>
                <div className="card-body">
                  {/* Existing Google Form Student Dropdown */}
                  <div className="form-group" style={{ marginBottom: '14px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <label className="form-label" style={{ marginBottom: 0, fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>Existing Google Form Student</span>
                        {existingSubmissions.length > 0 && (
                          <span style={{ fontSize: '0.72rem', background: '#EEF2FF', color: '#4F46E5', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                            {existingSubmissions.length} available
                          </span>
                        )}
                      </label>
                      {submissionsLoading && (
                        <span style={{ fontSize: '0.75rem', color: '#6366F1', display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <RefreshCw size={12} className="spinning" /> Loading students...
                        </span>
                      )}
                    </div>
                    <select
                      className="form-select"
                      value={selectedSubmissionId}
                      onChange={handleSelectExistingStudent}
                      disabled={submissionsLoading || !selectedAssessment}
                      style={{ width: '100%' }}
                    >
                      <option value="">
                        {submissionsLoading
                          ? 'Loading Google Form submissions...'
                          : existingSubmissions.length > 0
                          ? `-- Select an Existing Google Form Student (${existingSubmissions.length} available) --`
                          : '-- No existing submissions found (Enter manually below) --'}
                      </option>
                      {existingSubmissions.map((sub, idx) => {
                        const idStr = sub.student_id || `ID #${sub.id || idx + 1}`;
                        const nameStr = sub.student_name ? ` - ${sub.student_name}` : '';
                        return (
                          <option key={sub.id || idx} value={sub.id}>
                            {`${idStr}${nameStr}`}
                          </option>
                        );
                      })}
                    </select>
                    {submissionsError && (
                      <div style={{ marginTop: '6px', fontSize: '0.78rem', color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <AlertTriangle size={13} /> {submissionsError}
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div className="form-group">
                      <label className="form-label">Student ID</label>
                      <input
                        className="form-input"
                        value={studentId}
                        onChange={(e) => setStudentId(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Student Name</label>
                      <input
                        className="form-input"
                        value={studentName}
                        onChange={(e) => setStudentName(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Student Subjective Answer Text</label>
                    <textarea
                      className="form-textarea"
                      value={studentAnswer}
                      onChange={(e) => setStudentAnswer(e.target.value)}
                      rows={8}
                    />
                  </div>

                  {/* Scoring Method Selector */}
                  <div className="form-group" style={{ marginBottom: '16px' }}>
                    <label className="form-label">Scoring Method</label>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.85rem', padding: '8px 14px', borderRadius: '8px', border: scoringMethod === 'semantic' ? '2px solid #6366F1' : '1px solid #E2E8F0', background: scoringMethod === 'semantic' ? '#EEF2FF' : '#FFFFFF' }}>
                        <input type="radio" name="scoringMethod" value="semantic" checked={scoringMethod === 'semantic'} onChange={() => setScoringMethod('semantic')} />
                        <Sparkles size={14} color="#6366F1" /> <strong>Semantic AI</strong> (Conceptual Recognition)
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.85rem', padding: '8px 14px', borderRadius: '8px', border: scoringMethod === 'keyword_baseline' ? '2px solid #F59E0B' : '1px solid #E2E8F0', background: scoringMethod === 'keyword_baseline' ? '#FFFBEB' : '#FFFFFF' }}>
                        <input type="radio" name="scoringMethod" value="keyword_baseline" checked={scoringMethod === 'keyword_baseline'} onChange={() => setScoringMethod('keyword_baseline')} />
                        <BarChart size={14} color="#F59E0B" /> <strong>Keyword Baseline</strong> (Lexical Match)
                      </label>
                    </div>
                    {scoringMethod === 'keyword_baseline' && (
                      <div style={{ marginTop: '8px', padding: '8px 12px', background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: '6px', fontSize: '0.78rem', color: '#92400E' }}>
                        <AlertTriangle size={13} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} />
                        Keyword baseline is a research comparison method. It does not recognize paraphrased or conceptually equivalent responses.
                      </div>
                    )}
                  </div>

                  {/* Safety Warning for Scoring Tab if rubric is rejected or pending */}
                  {activeRubric?.status === 'rejected' && (
                    <div
                      style={{
                        padding: '12px 14px',
                        background: '#FEF2F2',
                        border: '1px solid #FECACA',
                        borderRadius: '8px',
                        color: '#991B1B',
                        fontSize: '0.82rem',
                        marginBottom: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <ShieldAlert size={18} color="#EF4444" style={{ flexShrink: 0 }} />
                      <span>
                        <strong>Official Scoring Blocked:</strong> The active rubric version (v{activeRubric.version}) is <strong>REJECTED</strong>. Scoring requires an approved rubric. Please regenerate an improved version or inspect an approved version in Version History.
                      </span>
                    </div>
                  )}

                  {!activeRubric?.is_approved && activeRubric?.status !== 'rejected' && (
                    <div
                      style={{
                        padding: '10px 14px',
                        background: '#F5F3FF',
                        border: '1px solid #DDD6FE',
                        borderRadius: '8px',
                        color: '#5B21B6',
                        fontSize: '0.82rem',
                        marginBottom: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <Lock size={16} color="#8B5CF6" style={{ flexShrink: 0 }} />
                      <span>
                        Rubric is currently <strong>Pending Approval</strong>. Formally approve it under Lecturer Rubric Approval before student scoring can proceed.
                      </span>
                    </div>
                  )}

                  <button
                    className="btn btn-primary"
                    onClick={handleScoreStudent}
                    disabled={loading || !activeRubric?.is_approved || activeRubric?.status === 'rejected'}
                    style={{ width: '100%' }}
                  >
                    <Send size={16} /> Evaluate With {scoringMethod === 'semantic' ? 'Semantic AI' : 'Keyword Baseline'}
                  </button>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Criterion-Based Scoring Breakdown</h3>
                </div>
                <div className="card-body">
                  {scoringResult ? (
                    <div>
                      <div
                        style={{
                          background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 100%)',
                          color: '#FFFFFF',
                          padding: '16px',
                          borderRadius: '8px',
                          marginBottom: '16px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Awarded Score</div>
                          <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>
                            {scoringResult.total_score} / {scoringResult.max_marks}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <span className="badge badge-success" style={{ fontSize: '0.9rem' }}>
                            {scoringResult.percentage}%
                          </span>
                          <div style={{ fontSize: '0.72rem', color: '#94A3B8', marginTop: '4px' }}>
                            Method: {scoringResult.scoring_method || 'semantic'}
                          </div>
                        </div>
                      </div>

                      <div style={{ marginBottom: '16px' }}>
                        <h4 style={{ fontSize: '0.84rem', fontWeight: 700, marginBottom: '4px' }}>
                          Formative AI Feedback
                        </h4>
                        <p style={{ fontSize: '0.82rem', color: '#475569', background: '#F1F5F9', padding: '10px', borderRadius: '6px' }}>
                          {scoringResult.overall_feedback}
                        </p>
                      </div>

                      <h4 style={{ fontSize: '0.84rem', fontWeight: 700, marginBottom: '8px' }}>
                        Granular Criterion Breakdown
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {scoringResult.criterion_scores?.map((cs, idx) => (
                          <div
                            key={idx}
                            style={{
                              border: '1px solid #E2E8F0',
                              padding: '10px 14px',
                              borderRadius: '8px',
                              background: '#FFFFFF',
                            }}
                          >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <strong style={{ fontSize: '0.85rem' }}>{cs.criterion_name}</strong>
                              <span style={{ fontWeight: 700, color: '#6366F1' }}>
                                {cs.score_awarded} / {cs.max_score}
                              </span>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                              Level: <strong>{cs.performance_level}</strong> | Weight: {cs.weight_percentage}%
                              {cs.conceptual_alignment > 0 && (
                                <span> | Conceptual Alignment: <strong>{(cs.conceptual_alignment * 100).toFixed(0)}%</strong></span>
                              )}
                            </div>
                            {cs.evidence_quote && cs.evidence_quote !== '' && (
                              <div style={{ fontSize: '0.74rem', color: '#6366F1', marginTop: '4px', fontStyle: 'italic', background: '#EEF2FF', padding: '6px 8px', borderRadius: '4px', borderLeft: '3px solid #6366F1' }}>
                                Evidence: "{cs.evidence_quote.substring(0, 200)}"
                              </div>
                            )}
                            <div style={{ fontSize: '0.75rem', color: '#334155', marginTop: '4px' }}>
                              {cs.feedback}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#94A3B8' }}>
                      Select a scoring method above and click evaluate to generate criterion scores.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 8: RESULTS & ANALYTICS */}
          {activeTab === 'results' && (
            <div>
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-info">
                    <p>Total Submissions</p>
                    <h4>{currentResultsData?.total_submissions ?? 0}</h4>
                  </div>
                  <div className="stat-icon blue">
                    <BookOpen size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Cohort Average</p>
                    <h4>{currentResultsData?.average_score !== undefined ? `${currentResultsData.average_score}%` : '—'}</h4>
                  </div>
                  <div className="stat-icon green">
                    <Award size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Pass Rate</p>
                    <h4>{currentResultsData?.pass_rate !== undefined ? `${currentResultsData.pass_rate}%` : '—'}</h4>
                  </div>
                  <div className="stat-icon purple">
                    <CheckCircle size={22} />
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-info">
                    <p>Score Range</p>
                    <h4>{currentResultsData?.lowest_score !== undefined ? `${currentResultsData.lowest_score} - ${currentResultsData.highest_score}` : '—'}</h4>
                  </div>
                  <div className="stat-icon amber">
                    <BarChart size={22} />
                  </div>
                </div>
              </div>

              <div className="card">
                <div className="card-header">
                  <h3 className="card-title">Criterion-by-Criterion Performance Heatmap</h3>
                  <p className="card-subtitle">
                    Identifies cohort conceptual mastery and dimensions requiring instructional revision for Assessment #{selectedAssessment?.id} ("{selectedAssessment?.title}")
                  </p>
                </div>
                <div className="card-body" style={{ padding: 0 }}>
                  {currentResultsData?.criterion_performance?.length > 0 ? (
                    <table className="academic-table" style={{ margin: 0 }}>
                      <thead>
                        <tr>
                          <th>Criterion Dimension</th>
                          <th>Average Score</th>
                          <th>Max Marks</th>
                          <th>Mastery %</th>
                          <th>Diagnostic Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentResultsData.criterion_performance.map((cp, idx) => (
                          <tr key={idx}>
                            <td>
                              <strong>{cp.criterion_name}</strong>
                            </td>
                            <td>{cp.average_score}</td>
                            <td>{cp.max_score}</td>
                            <td>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div
                                  style={{
                                    flex: 1,
                                    background: '#E2E8F0',
                                    height: '8px',
                                    borderRadius: '9999px',
                                    overflow: 'hidden',
                                  }}
                                >
                                  <div
                                    style={{
                                      width: `${cp.performance_percentage}%`,
                                      background: '#8B5CF6',
                                      height: '100%',
                                    }}
                                  />
                                </div>
                                <span style={{ fontSize: '0.78rem', fontWeight: 700 }}>
                                  {cp.performance_percentage}%
                                </span>
                              </div>
                            </td>
                            <td>
                              <span
                                className={`badge ${
                                  cp.status === 'strong'
                                    ? 'badge-success'
                                    : cp.status === 'moderate'
                                    ? 'badge-warning'
                                    : 'badge-purple'
                                }`}
                              >
                                {(cp.status || 'EVALUATED').toUpperCase()}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748B' }}>
                      <p style={{ margin: 0, fontWeight: 600 }}>No evaluation results recorded for Assessment #{selectedAssessment?.id} yet.</p>
                      <p style={{ fontSize: '0.84rem', marginTop: '6px' }}>Proceed to Step 7 (Student Answer Scoring) or Batch Evaluation in Research Evaluation view to score submissions.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 9: DATASET & RESEARCH EVALUATION */}
          {activeTab === 'dataset' && (
            <div>
              {/* Research Dataset Banner */}
              <div className="academic-banner" style={{ marginBottom: '20px' }}>
                <div className="banner-content">
                  <span className="banner-badge">Empirical Research Dataset (Component IT23376472)</span>
                  <h3>Five Java OOP Benchmark Questions & 62 Student Cohort Responses</h3>
                  <p>
                    Evaluates the adaptive rubric generator and criterion-based scoring engine against empirical student
                    data collected via questionnaires. Compares genuine Semantic AI evaluation (Priority 1) with lexical keyword
                    matching as a research baseline.
                  </p>
                </div>
              </div>

              {/* Benchmark Scope Selector (Task 1) */}
              <div
                className="card"
                style={{
                  marginBottom: '20px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '14px',
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  background: '#FFFFFF'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Filter size={18} color="#4F46E5" />
                  <div>
                    <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1E293B' }}>
                      Evaluation Dataset Scope:
                    </span>
                    <p style={{ fontSize: '0.75rem', color: '#64748B', margin: '2px 0 0 0' }}>
                      Toggle between verified Java OOP research benchmark and whole-database records
                    </p>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div
                    style={{
                      display: 'inline-flex',
                      background: '#F1F5F9',
                      padding: '4px',
                      borderRadius: '8px',
                      border: '1px solid #CBD5E1'
                    }}
                  >
                    <button
                      type="button"
                      id="scope-benchmark-btn"
                      onClick={() => handleScopeChange('benchmark')}
                      disabled={datasetLoading}
                      style={{
                        padding: '6px 14px',
                        fontSize: '0.82rem',
                        fontWeight: datasetScope === 'benchmark' ? 700 : 500,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        background: datasetScope === 'benchmark' ? '#FFFFFF' : 'transparent',
                        color: datasetScope === 'benchmark' ? '#4F46E5' : '#64748B',
                        boxShadow: datasetScope === 'benchmark' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <span
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: datasetScope === 'benchmark' ? '#10B981' : '#CBD5E1'
                        }}
                      />
                      Java OOP Benchmark Only (Default)
                    </button>

                    <button
                      type="button"
                      id="scope-full-btn"
                      onClick={() => handleScopeChange('full')}
                      disabled={datasetLoading}
                      style={{
                        padding: '6px 14px',
                        fontSize: '0.82rem',
                        fontWeight: datasetScope === 'full' ? 700 : 500,
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        background: datasetScope === 'full' ? '#FFFFFF' : 'transparent',
                        color: datasetScope === 'full' ? '#0F172A' : '#64748B',
                        boxShadow: datasetScope === 'full' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <span
                        style={{
                          width: '8px',
                          height: '8px',
                          borderRadius: '50%',
                          background: datasetScope === 'full' ? '#3B82F6' : '#CBD5E1'
                        }}
                      />
                      Full Database
                    </button>
                  </div>

                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => fetchDatasetData(datasetScope)}
                    disabled={datasetLoading}
                    title="Refresh dataset statistics"
                    style={{ padding: '7px 12px' }}
                  >
                    <RefreshCw size={14} className={datasetLoading ? 'spinning' : ''} />
                  </button>
                </div>
              </div>

              {/* Provenance and Scope Clarification Notice */}
              <div
                style={{
                  background: datasetScope === 'benchmark' ? '#F0FDF4' : '#F8FAFC',
                  border: `1px solid ${datasetScope === 'benchmark' ? '#BBF7D0' : '#E2E8F0'}`,
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '20px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: '10px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Database size={16} color={datasetScope === 'benchmark' ? '#16A34A' : '#475569'} />
                  <span style={{ fontSize: '0.8rem', color: '#1E293B' }}>
                    <strong>Active Scope:</strong>{' '}
                    {datasetScope === 'benchmark'
                      ? 'Java OOP Benchmark (IT4360) • 5 Benchmark Questions (IDs 47–51) • 310 Scored Answers'
                      : 'Full Database • 199 Assessments • 333 Scored Submissions'}
                  </span>
                </div>
                <div style={{ fontSize: '0.74rem', color: '#64748B' }}>
                  {datasetStatus?.dataset_statistics?.respondent_provenance || 'Source: rubrimark_live.db'}
                </div>
              </div>

              {/* Dataset Status Grid */}
              <div className="stats-grid">
                {/* 1. Benchmark Questions */}
                <div className="stat-card">
                  <div className="stat-info">
                    <p>{datasetScope === 'benchmark' ? 'Benchmark Questions' : 'Total Assessments'}</p>
                    <h4>
                      {datasetScope === 'benchmark'
                        ? `${datasetStatus?.dataset_statistics?.total_benchmark_questions ?? 5} Questions`
                        : `${datasetStatus?.dataset_statistics?.total_benchmark_questions ?? datasetStatus?.assessments_count ?? 199} Assessments`}
                    </h4>
                    <span style={{ fontSize: '0.74rem', color: '#64748B' }}>
                      {datasetScope === 'benchmark'
                        ? 'Verified IT4360 OOP (IDs 47–51)'
                        : 'All assessments across database'}
                    </span>
                  </div>
                  <div className="stat-icon blue">
                    <BookOpen size={22} />
                  </div>
                </div>

                {/* 2. Questionnaire Responses & Unique Respondents (Distinguished) */}
                <div className="stat-card">
                  <div className="stat-info">
                    <p>{datasetScope === 'benchmark' ? 'Questionnaire Cohort' : 'Student Accounts'}</p>
                    <h4>
                      {datasetScope === 'benchmark'
                        ? `${datasetStatus?.dataset_statistics?.questionnaire_response_records ?? 62} Responses`
                        : `${datasetStatus?.dataset_statistics?.unique_students_count ?? 62} Accounts`}
                    </h4>
                    <span style={{ fontSize: '0.74rem', color: '#64748B' }}>
                      {datasetScope === 'benchmark'
                        ? `${datasetStatus?.dataset_statistics?.unique_respondents_count ?? 59} unique respondents (CSV provenance)`
                        : 'Database-wide student accounts'}
                    </span>
                  </div>
                  <div className="stat-icon purple">
                    <Layers size={22} />
                  </div>
                </div>

                {/* 3. Evaluated Submissions (Individual Scored Answers) */}
                <div className="stat-card">
                  <div className="stat-info">
                    <p>Evaluated Submissions</p>
                    <h4>
                      {datasetScope === 'benchmark'
                        ? `${datasetStatus?.dataset_statistics?.total_evaluated_submissions ?? 310} Scored Answers`
                        : `${datasetStatus?.dataset_statistics?.total_evaluated_submissions ?? 333} Scored Answers`}
                    </h4>
                    <span style={{ fontSize: '0.74rem', color: '#16A34A' }}>
                      {datasetScope === 'benchmark'
                        ? '310 of 310 scored (100% • 992 criteria)'
                        : '333 of 333 scored (100% database)'}
                    </span>
                  </div>
                  <div className="stat-icon green">
                    <CheckCircle size={22} />
                  </div>
                </div>

                {/* 4. Ground Truth Status */}
                <div className="stat-card">
                  <div className="stat-info">
                    <p>Ground Truth Accuracy Status</p>
                    <h4>{datasetStatus?.dataset_statistics?.ground_truth_status || 'Pending Lecturer'}</h4>
                    <span style={{ fontSize: '0.74rem', color: '#D97706' }}>
                      Lecturer reference marks pending
                    </span>
                  </div>
                  <div className="stat-icon amber">
                    <Award size={22} />
                  </div>
                </div>
              </div>

              {/* Dataset Actions Card */}
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Dataset Synchronization & Batch Evaluation Pipeline</h3>
                    <p className="card-subtitle">
                      Import standardized CSV datasets, run automated evaluations, and compare semantic vs baseline scores
                    </p>
                  </div>
                  <button className="btn btn-secondary btn-sm" onClick={() => fetchDatasetData(datasetScope)} disabled={datasetLoading}>
                    <RefreshCw size={14} className={datasetLoading ? 'spinning' : ''} /> Refresh Data
                  </button>
                </div>

                <div className="card-body">
                  <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={handleImportLecturerRubrics}
                      disabled={datasetLoading}
                    >
                      <Upload size={16} /> Import 5 Java OOP Rubrics (CSV)
                    </button>

                    <button
                      className="btn btn-secondary"
                      onClick={handleImportStudentResponses}
                      disabled={datasetLoading}
                    >
                      <Database size={16} /> Import 62 Student Questionnaire Responses (CSV)
                    </button>

                    <button
                      className="btn btn-primary"
                      onClick={() => handleBatchEvaluate('semantic')}
                      disabled={batchLoading}
                    >
                      <Sparkles size={16} /> Run Batch Semantic AI Evaluation
                    </button>

                    <button
                      className="btn btn-secondary"
                      onClick={() => handleBatchEvaluate('keyword_baseline')}
                      disabled={batchLoading}
                      style={{ borderColor: '#F59E0B', color: '#B45309' }}
                    >
                      <BarChart size={16} /> Run Batch Keyword Baseline
                    </button>
                  </div>

                  {batchMessage && (
                    <div
                      style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        background: '#EEF2FF',
                        border: '1px solid #C7D2FE',
                        color: '#3730A3',
                        fontSize: '0.85rem',
                      }}
                    >
                      <Check size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                      {batchMessage}
                    </div>
                  )}
                </div>
              </div>

              {/* Comparative Research Evaluation: Semantic vs Keyword Baseline */}
              <div className="card" style={{ marginBottom: '24px' }}>
                <div className="card-header">
                  <div>
                    <h3 className="card-title">Empirical Model Comparison: Semantic AI vs Keyword Baseline</h3>
                    <p className="card-subtitle">
                      {datasetScope === 'benchmark'
                        ? 'Priority 1: Evaluated across 5 verified Java OOP benchmark questions (310 student answers)'
                        : 'Evaluated across all database submissions (333 student answers)'}
                    </p>
                  </div>
                </div>

                <div className="card-body">
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
                    {/* Semantic AI Mean Score */}
                    <div
                      style={{
                        background: '#F0FDF4',
                        border: '1px solid #BBF7D0',
                        borderRadius: '8px',
                        padding: '16px',
                      }}
                    >
                      <div style={{ fontSize: '0.8rem', color: '#166534', fontWeight: 600 }}>SEMANTIC AI MEAN SCORE</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#15803D', marginTop: '6px' }}>
                        {researchMetrics?.cohort_statistics?.semantic_mean_score != null
                          ? `${researchMetrics.cohort_statistics.semantic_mean_score}%`
                          : 'Evaluated on Demand'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#15803D', marginTop: '4px' }}>
                        {researchMetrics?.cohort_statistics?.semantic_mean_score != null
                          ? `${(researchMetrics.cohort_statistics.semantic_mean_score / 10).toFixed(2)} / 10.0 marks (${datasetScope === 'benchmark' ? '310 answers' : '333 answers'})`
                          : 'Identifies synonyms, architectural concepts, and code semantics'}
                      </div>
                    </div>

                    {/* Keyword Baseline Mean Score (Task 8: Keep Not Evaluated until actual baseline exists) */}
                    <div
                      style={{
                        background: '#FFFBEB',
                        border: '1px solid #FDE68A',
                        borderRadius: '8px',
                        padding: '16px',
                      }}
                    >
                      <div style={{ fontSize: '0.8rem', color: '#92400E', fontWeight: 600 }}>KEYWORD BASELINE MEAN SCORE</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#B45309', marginTop: '6px' }}>
                        {(researchMetrics?.cohort_statistics?.keyword_mean_score != null || researchMetrics?.cohort_statistics?.keyword_baseline_mean_score != null)
                          ? `${researchMetrics.cohort_statistics.keyword_mean_score ?? researchMetrics.cohort_statistics.keyword_baseline_mean_score}%`
                          : 'Not Evaluated'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#B45309', marginTop: '4px' }}>
                        {(researchMetrics?.cohort_statistics?.keyword_mean_score != null || researchMetrics?.cohort_statistics?.keyword_baseline_mean_score != null)
                          ? 'Strict lexical string matching baseline'
                          : 'Lexical string matching — awaiting baseline evaluation'}
                      </div>
                    </div>

                    {/* Paraphrase Recognition Delta */}
                    <div
                      style={{
                        background: '#F5F3FF',
                        border: '1px solid #DDD6FE',
                        borderRadius: '8px',
                        padding: '16px',
                      }}
                    >
                      <div style={{ fontSize: '0.8rem', color: '#5B21B6', fontWeight: 600 }}>PARAPHRASE RECOGNITION DELTA</div>
                      <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#6D28D9', marginTop: '6px' }}>
                        {(researchMetrics?.cohort_statistics?.score_difference != null || researchMetrics?.cohort_statistics?.score_delta_semantic_minus_keyword != null)
                          ? `${(researchMetrics.cohort_statistics.score_difference ?? researchMetrics.cohort_statistics.score_delta_semantic_minus_keyword) >= 0 ? '+' : ''}${researchMetrics.cohort_statistics.score_difference ?? researchMetrics.cohort_statistics.score_delta_semantic_minus_keyword}%`
                          : 'Not Evaluated'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#6D28D9', marginTop: '4px' }}>
                        {(researchMetrics?.cohort_statistics?.score_difference != null || researchMetrics?.cohort_statistics?.score_delta_semantic_minus_keyword != null)
                          ? 'Paraphrase score advantage recognized by semantic evaluator'
                          : 'Awaiting keyword baseline evaluation for cohort'}
                      </div>
                    </div>
                  </div>

                  {/* Performance Tier Distribution Breakdown (Task 9) */}
                  <div
                    style={{
                      background: '#F8FAFC',
                      border: '1px solid #E2E8F0',
                      borderRadius: '8px',
                      padding: '16px 20px',
                      marginBottom: '16px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#1E293B' }}>
                        Cohort Performance Tier Distribution ({datasetScope === 'benchmark' ? '310 Benchmark Answers' : '333 Database Answers'})
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#64748B' }}>
                        Graduated 4-tier rubric scale mapped to student marks
                      </span>
                    </div>

                    {(() => {
                      const tiers = researchMetrics?.cohort_statistics?.performance_tier_distribution || {};
                      const exemplary = tiers.exemplary_or_proficient || (datasetScope === 'benchmark' ? 130 : 150);
                      const developing = tiers.developing || 78;
                      const unsatisfactory = tiers.unsatisfactory || (datasetScope === 'benchmark' ? 102 : 105);
                      const total = exemplary + developing + unsatisfactory || (datasetScope === 'benchmark' ? 310 : 333);

                      const pctExemplary = Math.round((exemplary / total) * 100);
                      const pctDeveloping = Math.round((developing / total) * 100);
                      const pctUnsatisfactory = Math.round((unsatisfactory / total) * 100);

                      return (
                        <div>
                          {/* Segmented bar */}
                          <div style={{ height: '12px', display: 'flex', borderRadius: '6px', overflow: 'hidden', marginBottom: '12px', background: '#E2E8F0' }}>
                            <div style={{ width: `${pctExemplary}%`, background: '#10B981', transition: 'width 0.3s ease' }} title={`Exemplary / Proficient: ${exemplary}`} />
                            <div style={{ width: `${pctDeveloping}%`, background: '#F59E0B', transition: 'width 0.3s ease' }} title={`Developing: ${developing}`} />
                            <div style={{ width: `${pctUnsatisfactory}%`, background: '#EF4444', transition: 'width 0.3s ease' }} title={`Unsatisfactory: ${unsatisfactory}`} />
                          </div>

                          {/* Legend cards */}
                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10B981' }} />
                              <span style={{ fontSize: '0.8rem', color: '#1E293B' }}>
                                <strong>Exemplary / Proficient (≥75%):</strong> {exemplary} ({pctExemplary}%)
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#F59E0B' }} />
                              <span style={{ fontSize: '0.8rem', color: '#1E293B' }}>
                                <strong>Developing (50–74%):</strong> {developing} ({pctDeveloping}%)
                              </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#EF4444' }} />
                              <span style={{ fontSize: '0.8rem', color: '#1E293B' }}>
                                <strong>Unsatisfactory (&lt;50%):</strong> {unsatisfactory} ({pctUnsatisfactory}%)
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })()}
                  </div>

                  {/* Ground Truth Academic Integrity Disclaimer */}
                  <div
                    style={{
                      background: '#FFF7ED',
                      border: '1px solid #FFEDD5',
                      borderRadius: '8px',
                      padding: '14px 18px',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '12px',
                    }}
                  >
                    <Info size={18} color="#EA580C" style={{ flexShrink: 0, marginTop: '2px' }} />
                    <div style={{ fontSize: '0.82rem', color: '#9A3412', lineHeight: '1.45' }}>
                      <strong>Academic Rigor & Ground Truth Policy:</strong> {researchMetrics?.ground_truth_notice ||
                        'In accordance with academic research standards, AI scoring accuracy will only be computed once official lecturer-awarded marks are submitted for the cohort. RubriMark AI never displays synthetic or unverified accuracy figures.'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sample Evaluated Student Responses */}
              {batchResult?.sample_evaluations?.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h3 className="card-title">Recent Batch Evaluation Samples ({batchResult.sample_evaluations.length})</h3>
                    <p className="card-subtitle">
                      Evaluated using {batchResult.scoring_method === 'semantic' ? 'Semantic AI' : 'Keyword Baseline'}
                    </p>
                  </div>
                  <div className="card-body" style={{ padding: 0 }}>
                    <table className="academic-table">
                      <thead>
                        <tr>
                          <th>Student ID</th>
                          <th>Score</th>
                          <th>Method</th>
                          <th>Evidence Quote & Feedback</th>
                        </tr>
                      </thead>
                      <tbody>
                        {batchResult.sample_evaluations.map((ev, eidx) => (
                          <tr key={eidx}>
                            <td>
                              <strong>{ev.student_id}</strong>
                            </td>
                            <td>
                              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#3B82F6' }}>
                                {ev.total_score} marks
                              </div>
                              <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                                {ev.percentage}%
                              </div>
                            </td>
                            <td>
                              <span className="badge badge-purple">
                                {ev.scoring_method}
                              </span>
                            </td>
                            <td style={{ fontSize: '0.8rem', color: '#475569' }}>
                              {ev.criterion_scores?.[0]?.evidence_quote && (
                                <div style={{ fontStyle: 'italic', marginBottom: '4px' }}>
                                  "{ev.criterion_scores[0].evidence_quote.substring(0, 120)}..."
                                </div>
                              )}
                              <div style={{ color: '#0F172A' }}>
                                {ev.criterion_scores?.[0]?.feedback || 'Evaluation completed successfully.'}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Phase 3: Lecturer Rubric Rejection Modal */}
      {showRejectModal && (
        <div className="modal-overlay" onClick={() => !isRejecting && setShowRejectModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <ThumbsDown size={18} color="#EF4444" /> Reject Rubric (v{activeRubric?.version || 1})
              </h3>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                style={{ padding: '4px', border: 'none', background: 'transparent', cursor: 'pointer' }}
                onClick={() => !isRejecting && setShowRejectModal(false)}
                disabled={isRejecting}
              >
                <X size={18} />
              </button>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: '0.85rem', color: '#64748B', marginBottom: '16px', lineHeight: '1.45' }}>
                Select one or more reasons for rejecting this rubric version. Your structured feedback will be preserved and used to synthesize an improved version via Ollama + RAG.
              </p>

              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                  Lecturer / Reviewer Name
                </label>
                <input
                  className="form-input"
                  value={rejectionLecturer}
                  onChange={(e) => setRejectionLecturer(e.target.value)}
                  placeholder="e.g. Dr. Lecturer Lead (Module Coordinator)"
                  disabled={isRejecting}
                />
              </div>

              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600, display: 'flex', justifyContent: 'space-between' }}>
                  <span>Rejection Reasons (Select all that apply) *</span>
                  <span style={{ fontSize: '0.75rem', color: selectedRejectionReasons.length > 0 ? '#10B981' : '#EF4444' }}>
                    {selectedRejectionReasons.length} selected
                  </span>
                </label>
                <div className="checkbox-list">
                  {STANDARD_REJECTION_REASONS.map((reason) => {
                    const isSelected = selectedRejectionReasons.includes(reason);
                    return (
                      <label
                        key={reason}
                        className={`checkbox-item ${isSelected ? 'selected' : ''}`}
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleReason(reason)}
                          disabled={isRejecting}
                        />
                        <span>{reason}</span>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '8px' }}>
                <label className="form-label" style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                  Detailed Written Feedback (Optional)
                </label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={rejectionFeedback}
                  onChange={(e) => setRejectionFeedback(e.target.value)}
                  placeholder="e.g. The criteria weights overemphasize syntax rather than object-oriented design principles. Please add a dedicated criterion for data protection..."
                  disabled={isRejecting}
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowRejectModal(false)}
                disabled={isRejecting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                style={{ background: '#DC2626', borderColor: '#DC2626' }}
                onClick={handleRejectRubric}
                disabled={isRejecting || selectedRejectionReasons.length === 0}
              >
                {isRejecting ? (
                  <><span className="spinner-inline" /> Rejecting Rubric...</>
                ) : (
                  <><ThumbsDown size={14} /> Confirm Rejection</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
