"use client";

import { use } from "react";
import Link from "next/link";
import { PageHeader } from "@/shared/ui/page-header";
import { Skeleton } from "@/shared/ui/skeleton";
import { ErrorState } from "@/shared/ui/error-state";
import { Button } from "@/shared/ui/button";
import { useTranscript } from "@/modules/transcripts/hooks";
import { formatDate } from "@/shared/utils/format";
import { FileText, ChevronLeft } from "lucide-react";

export default function TranscriptPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: transcript, isLoading, error, refetch } = useTranscript(id);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-16 rounded-lg" />
        <Skeleton className="h-64 rounded-lg" />
      </div>
    );
  }
  if (error || !transcript) return <ErrorState title="Transcript not found" onRetry={refetch} />;

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Link href={`/console/students/${id}`}>
          <Button variant="ghost" size="sm">
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </Link>
        <PageHeader
          title="Transcript"
          description={`${transcript.student_name} · ${transcript.student_number}`}
          icon={FileText}
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-3 text-sm">
        <div className="rounded-lg border bg-card p-3">
          <p className="text-xs text-muted-foreground">GPA</p>
          <p className="font-semibold text-lg">{transcript.gpa?.toFixed(2) ?? "—"}</p>
        </div>
        <div className="rounded-lg border bg-card p-3">
          <p className="text-xs text-muted-foreground">Credits</p>
          <p className="font-semibold text-lg">{transcript.total_credits}</p>
        </div>
        <div className="rounded-lg border bg-card p-3">
          <p className="text-xs text-muted-foreground">Program</p>
          <p className="font-semibold text-sm">{transcript.program ?? "—"}</p>
        </div>
      </div>

      <div className="rounded-lg border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-2 text-left font-medium">Course</th>
              <th className="px-4 py-2 text-left font-medium">Section</th>
              <th className="px-4 py-2 text-left font-medium">Semester</th>
              <th className="px-4 py-2 text-center font-medium">Credits</th>
              <th className="px-4 py-2 text-center font-medium">Grade</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {transcript.entries.map((e, i) => (
              <tr key={i} className={e.completed ? "" : "text-muted-foreground"}>
                <td className="px-4 py-2">{e.course_name}</td>
                <td className="px-4 py-2">
                  <code className="text-xs">{e.section_code}</code>
                </td>
                <td className="px-4 py-2">{e.semester}</td>
                <td className="px-4 py-2 text-center">{e.credits}</td>
                <td className="px-4 py-2 text-center font-medium">{e.grade_value ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">Generated {formatDate(transcript.generated_at)}</p>
    </div>
  );
}
