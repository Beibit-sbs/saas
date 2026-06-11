export const QUALITY_ACCREDITATION_BOUNDARY_LABELS = {
  metadataEvidenceOnlyFoundation: 'Metadata/evidence-only quality foundation',
  readinessNotApproval: 'Accreditation readiness, not accreditation approval',
  evidenceMetadataOnly: 'Evidence metadata only',
  humanReviewRequired: 'Human review required',
  noOfficialAccreditationApproval: 'No official accreditation approval',
  noOfficialMinistrySubmission: 'No official ministry submission',
  noOfficialRankingClaim: 'No official ranking claim',
  noAutomaticAccreditationDecision: 'No automatic accreditation decision',
  noFakeAccreditationEvidence: 'No fake accreditation evidence',
  noFakeQualityScore: 'No fake quality score',
  noFakeSurveyResults: 'No fake survey results',
  noHiddenProgramScore: 'No hidden program score',
  noHiddenFacultyScore: 'No hidden faculty score',
  noHiddenStudentScore: 'No hidden student score',
  noProviderSync: 'No provider sync',
  noExternalDatabaseSync: 'No external database sync',
  fakeMetricsFalse: 'fake_metrics=false',
  fakeEvidenceFalse: 'fake_evidence=false',
  incompleteDataSupported: 'incomplete_data supported',
  readOnlyFirstBridge: 'Read-only-first bridge',
  runtimeShellPage:
    'Runtime shell is read-only and aggregator-only. It provides visibility across overview, readiness, evidence, risk, and dashboard without mutation.',
  accreditationRegistryPage:
    'Accreditation registry is read-only and aggregator-only. It summarizes accreditation metadata without provider integrations or write operations.',
  accreditationEvidencePage:
    'Accreditation evidence runtime is read-only and aggregator-only. It summarizes evidence inventory and readiness visibility without provider integrations or write operations.',
  correctiveActionRuntimePage:
    'Corrective action runtime is read-only and aggregator-only. It summarizes remediation progress, overdue posture, and risk without provider integrations or write operations.',
  dashboardPage:
    'fake_metrics=false. Data source: computed_from_quality_accreditation_metadata. Readiness is metadata-only and requires human review.',
  standardsPage:
    'Standards mapping is internal readiness metadata only. It does not approve accreditation or confirm official compliance.',
  evidencePage:
    'Evidence records are metadata-only unless reviewed by humans. No external/provider verification or official submission is claimed.',
  programReadinessPage:
    'Program readiness is an internal review signal, not an official accreditation decision or hidden program score.',
  institutionalReadinessPage:
    'Institutional readiness is evidence-backed metadata for internal review. No official ministry submission is performed.',
  selfAssessmentPage:
    'Self-assessment reports are draft/internal review artifacts only. No official submission is performed.',
  selfAssessmentRuntimePage:
    'Self-assessment runtime is read-only and aggregator-only. It summarizes standards readiness, coverage, and risk without provider integrations or write operations.',
  improvementPlanRuntimePage:
    'Improvement plan runtime is read-only and aggregator-only. It summarizes initiatives, milestones, KPI targets, progress, and forecast visibility without provider integrations or write operations.',
  auditFindingsRuntimePage:
    'Audit findings runtime is read-only and aggregator-only. It summarizes findings, non-conformities, recommendations, remediation, closure tracking, and readiness indicators without provider integrations or write operations.',
  readinessMonitoringRuntimePage:
    'Readiness monitoring runtime is read-only and aggregator-only. It summarizes readiness posture, risk, remediation progress, and indicators without provider integrations, background jobs, or write operations.',
  dashboardRuntimePage:
    'Dashboard runtime is read-only and aggregator-only. It consolidates accreditation/evidence/self-assessment/corrective/improvement/readiness/audit/KPI/compliance/risk indicators without provider mutations or workflow execution.',
  improvementPlansPage:
    'Improvement plans track human-owned actions. No autonomous sanction or automatic program closure is performed.',
  internalAuditsPage:
    'Internal quality audit records are human-review artifacts. No automatic penalty or hidden score is created.',
  programReviewPage:
    'Program review remains metadata-only. No automatic program closure or official accreditation approval is performed.',
  learningOutcomesPage:
    'Learning outcomes evidence remains metadata-only. No automatic grading or hidden scoring is performed.',
  stakeholderFeedbackPage:
    'Feedback metadata does not create fake survey results or hidden student/faculty/program scores.',
  committeePage:
    'Committee workflow records human decisions only. No automatic accreditation approval is performed.',
  externalReviewPage:
    'External review metadata does not claim fake expert approval or official external verification.',
  gapAnalysisPage:
    'Gap analysis is deterministic metadata for human review. It is not a hidden quality score.',
  calendarPage:
    'Calendar items track internal milestones only. No official deadline submission or provider sync is performed.',
  riskRegisterPage:
    'Risk register entries track human-owned mitigations only. No automated sanction or automatic closure is performed.',
  bridgesPage: 'Read-only-first bridge. No cross-suite mutation or provider sync is allowed by default.',
  limitationsPage:
    'Frontend runtime is not production-ready. Provider integrations, official approval, ministry submission, ranking claims, and L5/L6 readiness are not implemented.',
} as const;

export const QUALITY_ACCREDITATION_BOUNDARY_COPY = [
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.metadataEvidenceOnlyFoundation,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.evidenceMetadataOnly,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialAccreditationApproval,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialMinistrySubmission,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialRankingClaim,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noAutomaticAccreditationDecision,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeAccreditationEvidence,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeQualityScore,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeSurveyResults,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenProgramScore,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenFacultyScore,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenStudentScore,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noProviderSync,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.noExternalDatabaseSync,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeMetricsFalse,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeEvidenceFalse,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.incompleteDataSupported,
  QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
] as const;

export const QUALITY_ACCREDITATION_PAGE_BOUNDARY_LABELS = {
  runtimeShell: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.runtimeShellPage,
  ],
  accreditationRegistry: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.accreditationRegistryPage,
  ],
  accreditationEvidence: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.accreditationEvidencePage,
  ],
  correctiveActions: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.correctiveActionRuntimePage,
  ],
  overview: [...QUALITY_ACCREDITATION_BOUNDARY_COPY],
  dashboard: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeMetricsFalse,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.fakeEvidenceFalse,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.incompleteDataSupported,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.dashboardPage,
  ],
  standards: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialAccreditationApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.standardsPage,
  ],
  evidence: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.evidenceMetadataOnly,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeAccreditationEvidence,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.evidencePage,
  ],
  programReadiness: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenProgramScore,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.programReadinessPage,
  ],
  institutionalReadiness: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialMinistrySubmission,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.institutionalReadinessPage,
  ],
  selfAssessment: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialMinistrySubmission,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.selfAssessmentRuntimePage,
  ],
  improvementPlanRuntime: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.improvementPlanRuntimePage,
  ],
  auditFindingsRuntime: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.auditFindingsRuntimePage,
  ],
  readinessMonitoringRuntime: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessMonitoringRuntimePage,
  ],
  dashboardRuntime: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.dashboardRuntimePage,
  ],
  improvementPlans: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noAutomaticAccreditationDecision,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.improvementPlansPage,
  ],
  internalAudits: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenProgramScore,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.internalAuditsPage,
  ],
  programReview: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readinessNotApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noAutomaticAccreditationDecision,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.programReviewPage,
  ],
  learningOutcomes: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenProgramScore,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.learningOutcomesPage,
  ],
  stakeholderFeedback: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noFakeSurveyResults,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenStudentScore,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.stakeholderFeedbackPage,
  ],
  committee: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noAutomaticAccreditationDecision,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.committeePage,
  ],
  externalReview: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialAccreditationApproval,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.externalReviewPage,
  ],
  gapAnalysis: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noHiddenProgramScore,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.gapAnalysisPage,
  ],
  calendar: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noOfficialMinistrySubmission,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.calendarPage,
  ],
  riskRegister: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.humanReviewRequired,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noAutomaticAccreditationDecision,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.riskRegisterPage,
  ],
  bridges: [
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.readOnlyFirstBridge,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.noProviderSync,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.bridgesPage,
  ],
  limitations: [
    ...QUALITY_ACCREDITATION_BOUNDARY_COPY,
    QUALITY_ACCREDITATION_BOUNDARY_LABELS.limitationsPage,
  ],
} as const;

export type QualityAccreditationPageKey = keyof typeof QUALITY_ACCREDITATION_PAGE_BOUNDARY_LABELS;