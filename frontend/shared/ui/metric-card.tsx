import { Card, CardContent, CardHeader } from "./card";
import { Skeleton } from "./skeleton";
import type { LucideIcon } from "lucide-react";
import { cn } from "../utils/cn";

interface MetricCardProps {
  label: string;
  value: string | number | null | undefined;
  icon?: LucideIcon;
  description?: string;
  className?: string;
  loading?: boolean;
  trend?: "up" | "down" | "neutral";
}

export function MetricCard({ label, value, icon: Icon, description, className, loading, trend }: MetricCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <p className="text-sm font-medium text-muted-foreground">{label}</p>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <div className="text-2xl font-bold">{value ?? "—"}</div>
        )}
        {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
      </CardContent>
    </Card>
  );
}
