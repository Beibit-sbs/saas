'use client';

import { Button } from '@/shared/ui/button';

export function ExportButton({
  exportAvailable,
  onExport,
  unavailableReason = 'Export endpoint unavailable for this surface.',
}: {
  exportAvailable: boolean;
  onExport?: () => void;
  unavailableReason?: string;
}) {
  return (
    <Button
      variant="outline"
      onClick={onExport}
      disabled={!exportAvailable}
      title={!exportAvailable ? unavailableReason : undefined}
      data-testid="ui-framework-export-button"
    >
      Export
    </Button>
  );
}