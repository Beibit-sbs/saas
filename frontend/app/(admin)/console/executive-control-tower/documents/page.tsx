'use client';

import { RequirePermission } from '@/shared/ui/permission-gate';
import { ErrorState, LoadingState } from '@/shared/ui/page-states';
import {
  ControlTowerShell,
  CorrespondenceWorkflowPanel,
  DataSourceGuardPanel,
  DecreeWorkflowPanel,
  DocumentWorkflowPanel,
} from '@/modules/executive-control-tower/components';
import {
  useCorrespondenceWorkflowSummary,
  useDecreeWorkflowSummary,
  useDocumentWorkflowSummary,
} from '@/modules/executive-control-tower/hooks';
import { EXECUTIVE_CONTROL_TOWER_PERMISSIONS } from '@/modules/executive-control-tower/permissions';

export default function ExecutiveControlTowerDocumentsPage() {
  const documents = useDocumentWorkflowSummary();
  const decrees = useDecreeWorkflowSummary();
  const correspondence = useCorrespondenceWorkflowSummary();

  if (documents.isPending || decrees.isPending || correspondence.isPending) {
    return <LoadingState title="Loading document workflow metrics" />;
  }

  const untrustedError = [documents, decrees, correspondence].find(
    (query) => query.isUntrusted && query.error instanceof Error,
  )?.error;
  if (untrustedError instanceof Error) {
    return <DataSourceGuardPanel reason={untrustedError.message} />;
  }

  const runtimeError = [documents, decrees, correspondence].find((query) => query.error)?.error;
  if (runtimeError) {
    return <ErrorState error={runtimeError} message="Failed to load document workflow panels." />;
  }

  if (!documents.data || !decrees.data || !correspondence.data) {
    return <ErrorState message="Document workflow panels are unavailable." />;
  }

  return (
    <RequirePermission permission={EXECUTIVE_CONTROL_TOWER_PERMISSIONS.DOCUMENTS_READ}>
      <ControlTowerShell
        title="Document Workflow"
        description="Read-only visibility across documents, decrees, and correspondence."
        activePath="/console/executive-control-tower/documents"
      >
        <div className="space-y-6">
          <DocumentWorkflowPanel summary={documents.data} />
          <DecreeWorkflowPanel summary={decrees.data} />
          <CorrespondenceWorkflowPanel summary={correspondence.data} />
        </div>
      </ControlTowerShell>
    </RequirePermission>
  );
}