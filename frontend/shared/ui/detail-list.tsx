import type { ReactNode } from "react";

interface DetailItem {
  label: string;
  value: ReactNode;
}

interface DetailListProps {
  items: DetailItem[];
}

export function DetailList({ items }: DetailListProps) {
  return (
    <dl className="space-y-4">
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{item.label}</dt>
          <dd className="text-sm text-foreground">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}