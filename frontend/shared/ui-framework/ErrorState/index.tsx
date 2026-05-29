'use client';

export function ErrorState({
  title = 'Unable to load this view',
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6" data-testid="ui-framework-error-state">
      <h3 className="text-lg font-semibold">{title}</h3>
      {description ? <p className="mt-2 text-sm text-muted-foreground">{description}</p> : null}
    </div>
  );
}