'use client';

import { Button } from '@/shared/ui/button';

export function EvidenceUploadPanel({
  uploadSupported,
  onSelectFile,
  limitationLabel = 'Evidence upload is metadata-first and requires backend endpoint support.',
}: {
  uploadSupported: boolean;
  onSelectFile?: () => void;
  limitationLabel?: string;
}) {
  return (
    <section className="rounded-lg border bg-background p-4" data-testid="ui-framework-evidence-upload-panel">
      <h3 className="text-base font-semibold">Evidence Upload</h3>
      <p className="mt-1 text-sm text-muted-foreground">Metadata-first upload surface.</p>
      <p className="mt-2 text-xs text-muted-foreground">{limitationLabel}</p>
      <Button
        className="mt-3"
        variant="outline"
        disabled={!uploadSupported}
        onClick={onSelectFile}
        title={!uploadSupported ? 'Upload endpoint unavailable for this surface.' : undefined}
      >
        Upload evidence
      </Button>
    </section>
  );
}