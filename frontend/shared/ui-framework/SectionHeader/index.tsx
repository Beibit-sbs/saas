'use client';

export function SectionHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <header className="space-y-2" data-testid="ui-framework-section-header">
      {eyebrow ? <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">{eyebrow}</p> : null}
      <h1 className="text-3xl font-semibold">{title}</h1>
      {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
    </header>
  );
}