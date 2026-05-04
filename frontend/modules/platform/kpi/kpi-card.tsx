"use client";

import { Card, CardContent, CardHeader } from "@/shared/ui/card";
import { cn } from "@/shared/utils/cn";
import type { RectorTrendPoint } from "./types";
import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";

type TrendDirection = "up" | "down" | "neutral";

interface KpiCardProps {
  title: string;
  value: number;
  trendPoints: RectorTrendPoint[];
  severityLevel?: "warning" | "critical" | null;
}

function toDirection(points: RectorTrendPoint[]): TrendDirection {
  if (points.length < 2) return "neutral";
  const first = Number(points[0]?.value ?? 0);
  const last = Number(points[points.length - 1]?.value ?? 0);
  if (last > first) return "up";
  if (last < first) return "down";
  return "neutral";
}

function toPolylinePoints(values: number[], width: number, height: number): string {
  if (values.length === 0) return "";
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(max - min, 1);

  return values
    .map((value, index) => {
      const x = values.length === 1 ? width / 2 : (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    })
    .join(" ");
}

function TrendBadge({ direction }: { direction: TrendDirection }) {
  if (direction === "up") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-600">
        <ArrowUpRight className="h-3.5 w-3.5" />
        Up
      </span>
    );
  }

  if (direction === "down") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-rose-500/10 px-2 py-0.5 text-xs font-medium text-rose-600">
        <ArrowDownRight className="h-3.5 w-3.5" />
        Down
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
      <ArrowRight className="h-3.5 w-3.5" />
      Flat
    </span>
  );
}

export function KpiCard({ title, value, trendPoints, severityLevel }: KpiCardProps) {
  const direction = toDirection(trendPoints);
  const values = trendPoints.map((point) => Number(point.value ?? 0));
  const polyline = toPolylinePoints(values, 100, 28);

  return (
    <Card
      className={cn(
        severityLevel === "critical" && "border-l-4 border-l-rose-500",
        severityLevel === "warning" && "border-l-4 border-l-amber-500",
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <TrendBadge direction={direction} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold leading-none tracking-tight">{Number(value ?? 0).toLocaleString()}</div>
        <div className="mt-3 h-8 w-full">
          {values.length > 0 ? (
            <svg
              viewBox="0 0 100 28"
              preserveAspectRatio="none"
              className="h-8 w-full"
              role="img"
              aria-label={`${title} trend`}
            >
              <polyline
                fill="none"
                strokeWidth="2"
                points={polyline}
                className={cn(
                  "transition-colors",
                  direction === "up" && "stroke-emerald-500",
                  direction === "down" && "stroke-rose-500",
                  direction === "neutral" && "stroke-muted-foreground"
                )}
              />
            </svg>
          ) : (
            <div className="h-8 w-full rounded bg-muted/40" />
          )}
        </div>
      </CardContent>
    </Card>
  );
}
