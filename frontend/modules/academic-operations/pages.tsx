'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ACADEMIC_OPERATIONS_PAGE_TITLES,
  ACADEMIC_OPERATIONS_ROUTES,
} from './constants';
import {
  ACADEMIC_OPERATIONS_PERMISSIONS,
  getAcademicOperationsBoundaryLabels,
} from './guards';
import {
  useAcademicGroups,
  useAcademicOperationsAudit,
  useAcademicOperationsCanonicalReuseSummary,
  useAcademicOperationsDashboard,
  useAcademicOperationsEvidence,
  useAcademicOperationsHealth,
  useAcademicOperationsMatrixSummary,
  useAdvisorTutorAssignments,
  useBridges,
  useCohorts,
  useCourseRegistrationMetadata,
  useDocumentWorkflowBridgeSummary,
  useExecutiveGovernanceBridgeSummary,
  useGradebookMetadata,
  useQualityAccreditationBridgeSummary,
  useRetakePlans,
  useStudentLifecycleBridgeSummary,
  useSummerSemesterTerms,
} from './hooks';
import {
  AcademicGroupsRegistry,
  AcademicOperationsDashboard,
  AcademicOperationsShell,
  AdvisorTutorRegistry,
  AuditEvidencePanel,
  BridgeMetadataPanel,
  CanonicalReusePanel,
  CohortsRegistry,
  CourseRegistrationMetadataRegistry,
  GradebookMetadataRegistry,
  LimitationsPanel,
  MatrixSummaryPanel,
  RetakePlansRegistry,
  SummerSemesterRegistry,
} from './components';

function PageError(message: string, error: unknown) {
  return <ErrorState error={error} message={message} />;
}

function ModuleShell({
  title,
  description,
  currentPath,
  boundaryPage,
  children,
}: {
  title: string;
  description: string;
  currentPath: string;
  boundaryPage: Parameters<typeof getAcademicOperationsBoundaryLabels>[0];
  children: React.ReactNode;
}) {
  return (
    <AcademicOperationsShell
      title={title}
      description={description}
      currentPath={currentPath}
      boundaryLabels={getAcademicOperationsBoundaryLabels(boundaryPage)}
    >
      {children}
    </AcademicOperationsShell>
  );
}

export function AcademicOperationsOverviewPage() {
  const dashboard = useAcademicOperationsDashboard();
  const health = useAcademicOperationsHealth();
  const matrixSummary = useAcademicOperationsMatrixSummary();
  const canonicalReuseSummary = useAcademicOperationsCanonicalReuseSummary();

  if (dashboard.isPending || health.isPending || matrixSummary.isPending || canonicalReuseSummary.isPending) {
    return <LoadingState title="Loading Academic Operations overview" />;
  }

  if (dashboard.error) return PageError('Failed to load Academic Operations dashboard.', dashboard.error);
  if (health.error) return PageError('Failed to load Academic Operations health.', health.error);
  if (matrixSummary.error) return PageError('Failed to load Academic Operations matrix summary.', matrixSummary.error);
  if (canonicalReuseSummary.error) return PageError('Failed to load Academic Operations canonical reuse summary.', canonicalReuseSummary.error);

  if (!dashboard.data || !health.data || !matrixSummary.data) {
    return <ErrorState message="Academic Operations overview is unavailable." />;
  }

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.overviewRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.overview}
        description="Controlled frontend runtime for metadata registries, matrix visibility, canonical bridges, audit, and evidence."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.overview}
        boundaryPage="overview"
      >
        <AcademicOperationsDashboard
          dashboard={dashboard.data}
          health={health.data}
          matrixSummary={matrixSummary.data}
          canonicalReuseSummary={canonicalReuseSummary.data}
        />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsDashboardPage() {
  return <AcademicOperationsOverviewPage />;
}

export function AcademicOperationsMatrixPage() {
  const matrixSummary = useAcademicOperationsMatrixSummary();
  const canonicalReuseSummary = useAcademicOperationsCanonicalReuseSummary();

  if (matrixSummary.isPending || canonicalReuseSummary.isPending) {
    return <LoadingState title="Loading Academic Operations matrix" />;
  }
  if (matrixSummary.error) return PageError('Failed to load Academic Operations matrix summary.', matrixSummary.error);
  if (canonicalReuseSummary.error) return PageError('Failed to load Academic Operations canonical summary.', canonicalReuseSummary.error);
  if (!matrixSummary.data) return <ErrorState message="Academic Operations matrix summary is unavailable." />;

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.overviewRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.matrix}
        description="Matrix-guided contract visibility for the implemented subset of the Academic Operations backend."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.matrix}
        boundaryPage="matrix"
      >
        <div className="space-y-4">
          <MatrixSummaryPanel summary={matrixSummary.data} />
          <CanonicalReusePanel summary={canonicalReuseSummary.data} />
          <LimitationsPanel limitations={matrixSummary.data.required_limitations} />
        </div>
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsAcademicGroupsPage() {
  const groups = useAcademicGroups();
  if (groups.isPending) return <LoadingState title="Loading academic groups" />;
  if (groups.error) return PageError('Failed to load academic groups.', groups.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.academicGroupsRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.academicGroups}
        description="Academic group metadata with opaque references and explicit human-review boundaries."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.academicGroups}
        boundaryPage="academicGroups"
      >
        <AcademicGroupsRegistry groups={groups.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsCohortsPage() {
  const cohorts = useCohorts();
  if (cohorts.isPending) return <LoadingState title="Loading cohorts" />;
  if (cohorts.error) return PageError('Failed to load cohorts.', cohorts.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.cohortsRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.cohorts}
        description="Cohort metadata only. No official graduation or degree decisions are made here."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.cohorts}
        boundaryPage="cohorts"
      >
        <CohortsRegistry cohorts={cohorts.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsCourseRegistrationPage() {
  const courseRegistration = useCourseRegistrationMetadata();
  if (courseRegistration.isPending) return <LoadingState title="Loading course registration metadata" />;
  if (courseRegistration.error) return PageError('Failed to load course registration metadata.', courseRegistration.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.canonicalBridgeRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.courseRegistration}
        description="Course registration metadata with Student Lifecycle bridge awareness and no live SIS or Platonus sync."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.courseRegistration}
        boundaryPage="courseRegistration"
      >
        <CourseRegistrationMetadataRegistry items={courseRegistration.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsGradebookMetadataPage() {
  const gradebook = useGradebookMetadata();
  if (gradebook.isPending) return <LoadingState title="Loading gradebook metadata" />;
  if (gradebook.error) return PageError('Failed to load gradebook metadata.', gradebook.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.gradebookMetadataRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.gradebookMetadata}
        description="Gradebook structure metadata only with no grade calculation, publication, or approval UI."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.gradebookMetadata}
        boundaryPage="gradebook"
      >
        <GradebookMetadataRegistry items={gradebook.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsRetakesPage() {
  const retakes = useRetakePlans();
  if (retakes.isPending) return <LoadingState title="Loading retake plans" />;
  if (retakes.error) return PageError('Failed to load retake plans.', retakes.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.retakeManagementRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.retakes}
        description="Retake plan metadata with human review requirements and no sanction or dismissal automation."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.retakes}
        boundaryPage="retakes"
      >
        <RetakePlansRegistry items={retakes.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsSummerSemestersPage() {
  const terms = useSummerSemesterTerms();
  if (terms.isPending) return <LoadingState title="Loading summer semester terms" />;
  if (terms.error) return PageError('Failed to load summer semester terms.', terms.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.summerSemesterRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.summerSemesters}
        description="Summer semester term and window metadata without billing, provider, or auto-enrollment claims."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.summerSemesters}
        boundaryPage="summerSemesters"
      >
        <SummerSemesterRegistry terms={terms.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsAdvisorTutorPage() {
  const assignments = useAdvisorTutorAssignments();
  if (assignments.isPending) return <LoadingState title="Loading advisor and tutor assignments" />;
  if (assignments.error) return PageError('Failed to load advisor and tutor assignments.', assignments.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.advisorTutorRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.advisorTutor}
        description="Advisor and tutor assignment metadata with no hidden score or faculty ranking UI."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.advisorTutor}
        boundaryPage="advisorTutor"
      >
        <AdvisorTutorRegistry assignments={assignments.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsBridgesPage() {
  const bridges = useBridges();
  const studentLifecycle = useStudentLifecycleBridgeSummary();
  const documentWorkflow = useDocumentWorkflowBridgeSummary();
  const executiveGovernance = useExecutiveGovernanceBridgeSummary();
  const qualityAccreditation = useQualityAccreditationBridgeSummary();

  if (bridges.isPending || studentLifecycle.isPending || documentWorkflow.isPending || executiveGovernance.isPending || qualityAccreditation.isPending) {
    return <LoadingState title="Loading canonical bridge metadata" />;
  }

  if (bridges.error) return PageError('Failed to load canonical bridge registry.', bridges.error);
  if (studentLifecycle.error) return PageError('Failed to load Student Lifecycle bridge summary.', studentLifecycle.error);
  if (documentWorkflow.error) return PageError('Failed to load Document Workflow bridge summary.', documentWorkflow.error);
  if (executiveGovernance.error) return PageError('Failed to load Executive Governance bridge summary.', executiveGovernance.error);
  if (qualityAccreditation.error) return PageError('Failed to load Quality Accreditation bridge summary.', qualityAccreditation.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.canonicalBridgeRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.bridges}
        description="Bridge-first, canonical-aware view across reused capabilities and cross-suite references."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.bridges}
        boundaryPage="bridges"
      >
        <BridgeMetadataPanel
          bridges={bridges.data ?? []}
          studentLifecycle={studentLifecycle.data ?? []}
          documentWorkflow={documentWorkflow.data ?? []}
          executiveGovernance={executiveGovernance.data ?? []}
          qualityAccreditation={qualityAccreditation.data ?? []}
        />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsAuditEvidencePage() {
  const audit = useAcademicOperationsAudit();
  const evidence = useAcademicOperationsEvidence();

  if (audit.isPending || evidence.isPending) {
    return <LoadingState title="Loading audit and evidence metadata" />;
  }
  if (audit.error) return PageError('Failed to load audit metadata.', audit.error);
  if (evidence.error) return PageError('Failed to load evidence metadata.', evidence.error);

  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.auditRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.auditEvidence}
        description="Audit event and evidence metadata only. No legal, decree, or official evidence claims."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.auditEvidence}
        boundaryPage="auditEvidence"
      >
        <AuditEvidencePanel audit={audit.data ?? []} evidence={evidence.data ?? []} />
      </ModuleShell>
    </RequirePermission>
  );
}

export function AcademicOperationsLimitationsPage() {
  return (
    <RequirePermission permission={ACADEMIC_OPERATIONS_PERMISSIONS.overviewRead}>
      <ModuleShell
        title={ACADEMIC_OPERATIONS_PAGE_TITLES.limitations}
        description="Explicit no-overclaim boundaries and known runtime limitations for the Academic Operations frontend."
        currentPath={ACADEMIC_OPERATIONS_ROUTES.limitations}
        boundaryPage="limitations"
      >
        <LimitationsPanel />
      </ModuleShell>
    </RequirePermission>
  );
}