export const ACADEMIC_OPERATIONS_BOUNDARY_LABELS = {
  metadataOnlyFoundation: 'Metadata-only foundation',
  matrixGuidedPlanning: 'Matrix-guided: 467 planning rows',
  canonicalReuse: 'Canonical reuse / no duplicate modules',
  noOfficialGradePublication: 'No official grade publication',
  noOfficialTranscriptUpdate: 'No official transcript update',
  noAutomatedGrading: 'No automated grading',
  noAutomaticSanction: 'No automatic sanction',
  noHiddenScore: 'No hidden score',
  noProviderSync: 'No provider sync',
  noPlatonusSisIntegration: 'No Platonus/SIS integration',
  noFakeKpi: 'No fake KPI',
  humanReviewRequired: 'Human review required',
  readOnlyFirstBridge: 'Read-only-first bridge',
  gradebookPage: 'This page manages gradebook metadata only. It does not display, calculate, publish, or approve official grades.',
  retakesPage: 'Retake metadata requires human review. No automatic retake denial, sanction, or dismissal is performed.',
  bridgesPage: 'Read-only-first bridge. No cross-suite mutation is allowed by default.',
  dashboardPage: 'fake_metrics=false. Data source: computed_from_academic_operations_metadata.',
  noFakeEvidence: 'No fake evidence',
  noOfficialLegalDocumentClaim: 'No official legal document claim',
} as const;

export const ACADEMIC_OPERATIONS_BOUNDARY_COPY = [
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.matrixGuidedPlanning,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.canonicalReuse,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialGradePublication,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialTranscriptUpdate,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomatedGrading,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomaticSanction,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noHiddenScore,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noPlatonusSisIntegration,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noFakeKpi,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.humanReviewRequired,
  ACADEMIC_OPERATIONS_BOUNDARY_LABELS.readOnlyFirstBridge,
] as const;

export const ACADEMIC_OPERATIONS_PAGE_BOUNDARY_LABELS = {
  overview: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.matrixGuidedPlanning,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.dashboardPage,
  ],
  dashboard: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noFakeKpi,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.dashboardPage,
  ],
  matrix: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.matrixGuidedPlanning,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.canonicalReuse,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
  ],
  academicGroups: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.humanReviewRequired,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.canonicalReuse,
  ],
  cohorts: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.humanReviewRequired,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomaticSanction,
  ],
  courseRegistration: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noPlatonusSisIntegration,
  ],
  gradebook: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialGradePublication,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomatedGrading,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.gradebookPage,
  ],
  retakes: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.humanReviewRequired,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noAutomaticSanction,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.retakesPage,
  ],
  summerSemesters: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noProviderSync,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialGradePublication,
  ],
  advisorTutor: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.humanReviewRequired,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noHiddenScore,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
  ],
  bridges: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.canonicalReuse,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.readOnlyFirstBridge,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.bridgesPage,
  ],
  auditEvidence: [
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.metadataOnlyFoundation,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noFakeEvidence,
    ACADEMIC_OPERATIONS_BOUNDARY_LABELS.noOfficialLegalDocumentClaim,
  ],
  limitations: [...ACADEMIC_OPERATIONS_BOUNDARY_COPY],
} as const;

export type AcademicOperationsPageKey = keyof typeof ACADEMIC_OPERATIONS_PAGE_BOUNDARY_LABELS;