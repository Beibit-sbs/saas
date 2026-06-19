"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/shared/ui/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Button } from "@/shared/ui/button";
import { FileText, Search } from "lucide-react";
import { usePermissions } from "@/shared/hooks/use-permissions";
import { PERMISSIONS } from "@/shared/config/permissions";
import { AccessDenied } from "@/shared/ui/permission-gate";
import { useLanguage } from "@/app/components/LanguageProvider";
import { useStudents } from "@/modules/students/hooks";

export default function TranscriptsPage() {
  const { t } = useLanguage();
  const { hasPermission } = usePermissions();
  const router = useRouter();
  const [studentId, setStudentId] = useState("");
  const studentsQuery = useStudents({ page: 1, page_size: 200, status: "active" });
  const students = studentsQuery.data?.items ?? [];

  if (!hasPermission(PERMISSIONS.TRANSCRIPTS_READ)) return <AccessDenied />;

  function openTranscript() {
    if (!studentId.trim()) return;
    router.push(`/console/students/${studentId.trim()}/transcript`);
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <PageHeader
        title={t("nav.transcripts")}
        description={t("console.transcripts.description")}
        icon={FileText}
      />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Lookup</CardTitle>
          <CardDescription>Select a student profile and open the official transcript view.</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {students.length > 0 ? (
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={studentId}
              onChange={(event) => setStudentId(event.target.value)}
              data-testid="transcript-student-select"
            >
              <option value="">Select student</option>
              {students.map((student) => (
                <option key={student.id} value={student.id}>
                  {student.student_number} / {student.first_name} {student.last_name} (#{student.id})
                </option>
              ))}
            </select>
          ) : (
            <Input
              placeholder="Student profile ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") openTranscript();
              }}
            />
          )}
          <Button onClick={openTranscript}>
            <Search className="h-4 w-4 mr-1" />
            Open
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
