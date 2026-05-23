export const RESEARCH_SCIENCE_BOUNDARY_LABELS = {
  metadataOnlyResearchFoundation: 'Metadata-only research foundation',
  evidenceMetadataOnly: 'Evidence metadata only',
  humanReviewRequired: 'Human review required',
  noFakePublications: 'No fake publications',
  noFakeConferenceCertificates: 'No fake conference certificates',
  noFakeGrantEvidence: 'No fake grant evidence',
  noAutonomousEthicsApproval: 'No autonomous ethics approval',
  noAutonomousGrantSubmission: 'No autonomous grant submission',
  noAutonomousPublicationVerification: 'No autonomous publication verification',
  noHiddenResearcherScore: 'No hidden researcher score',
  noHiddenFacultyScore: 'No hidden faculty score',
  noHiddenStudentResearchScore: 'No hidden student research score',
  noProviderSync: 'No provider sync',
  noScopusWosOrcidSync: 'No Scopus/WoS/ORCID sync',
  noMinistrySync: 'No ministry sync',
  noExternalDatabaseSync: 'No external database sync',
  noOfficialVerification: 'No official verification',
  noOfficialRanking: 'No official ranking',
  noCitationScore: 'No citation score',
  fakeMetricsFalse: 'fake_metrics=false',
  incompleteDataSupported: 'incomplete_data supported',
  readOnlyFirstBridge: 'Read-only-first bridge',
  publicationsPage:
    'This page stores publication metadata only. It does not verify publications officially, calculate citation scores, or create fake publications.',
  conferencesPage:
    'This page stores conference participation metadata only. It does not create or validate official certificates.',
  grantsPage:
    'This page tracks grant metadata only. It does not submit grant applications or confirm official awards.',
  ethicsPage:
    'Ethics requests require human committee review. No autonomous ethics approval is performed.',
  evidencePage:
    'Evidence records are metadata-only unless reviewed by humans. No external/provider verification is claimed.',
  dashboardPage: 'fake_metrics=false. Data source: computed_from_research_science_metadata.',
  bridgesPage: 'Read-only-first bridge. No cross-suite mutation or provider sync is allowed by default.',
  limitationsPage:
    'Frontend runtime is not production-ready. Provider integrations, official verification, and the full Research / Science vertical remain deferred.',
} as const;

export const RESEARCH_SCIENCE_BOUNDARY_COPY = [
  RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.evidenceMetadataOnly,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakePublications,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakeConferenceCertificates,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakeGrantEvidence,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousEthicsApproval,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousGrantSubmission,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousPublicationVerification,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenResearcherScore,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenFacultyScore,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenStudentResearchScore,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noProviderSync,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noScopusWosOrcidSync,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noMinistrySync,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noExternalDatabaseSync,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialRanking,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.noCitationScore,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.fakeMetricsFalse,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.incompleteDataSupported,
  RESEARCH_SCIENCE_BOUNDARY_LABELS.readOnlyFirstBridge,
] as const;

export const RESEARCH_SCIENCE_PAGE_BOUNDARY_LABELS = {
  overview: [...RESEARCH_SCIENCE_BOUNDARY_COPY],
  dashboard: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.fakeMetricsFalse,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.incompleteDataSupported,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.dashboardPage,
  ],
  projects: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification,
  ],
  studentResearch: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenStudentResearchScore,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
  ],
  supervision: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noHiddenFacultyScore,
  ],
  publications: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakePublications,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousPublicationVerification,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noCitationScore,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.publicationsPage,
  ],
  conferences: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakeConferenceCertificates,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.conferencesPage,
  ],
  grants: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noFakeGrantEvidence,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousGrantSubmission,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.grantsPage,
  ],
  ethics: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noAutonomousEthicsApproval,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.ethicsPage,
  ],
  evidence: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.evidenceMetadataOnly,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.evidencePage,
  ],
  audit: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.humanReviewRequired,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.metadataOnlyResearchFoundation,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noOfficialVerification,
  ],
  bridges: [
    RESEARCH_SCIENCE_BOUNDARY_LABELS.readOnlyFirstBridge,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.noProviderSync,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.bridgesPage,
  ],
  limitations: [
    ...RESEARCH_SCIENCE_BOUNDARY_COPY,
    RESEARCH_SCIENCE_BOUNDARY_LABELS.limitationsPage,
  ],
} as const;

export type ResearchSciencePageKey = keyof typeof RESEARCH_SCIENCE_PAGE_BOUNDARY_LABELS;