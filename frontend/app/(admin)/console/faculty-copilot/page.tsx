"use client";

import { useState } from "react";
import { Bot } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useFacultyQnA,
  useGenerateLessonPlan,
  useGenerateMaterialPack,
} from "@/modules/faculty-copilot/hooks";

export default function FacultyCopilotPage() {
  const [facultyId, setFacultyId] = useState("FAC-001");
  const [courseTitle, setCourseTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [question, setQuestion] = useState("");

  const lessonPlan = useGenerateLessonPlan();
  const materialPack = useGenerateMaterialPack();
  const qna = useFacultyQnA();

  const lastAnswer = qna.data ?? materialPack.data ?? lessonPlan.data;
  const isBusy = lessonPlan.isPending || materialPack.isPending || qna.isPending;

  return (
    <RequirePermission permission={PERMISSIONS.FACULTY_COPILOT_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Faculty Copilot"
          subtitle="AI assistant for lesson plans, teaching materials, and faculty Q&A"
          icon={Bot}
        />

        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Inputs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="faculty_id">Faculty ID</Label>
              <Input
                id="faculty_id"
                value={facultyId}
                onChange={(e) => setFacultyId(e.target.value)}
                placeholder="FAC-001"
              />
            </div>
            <div>
              <Label htmlFor="course_title">Course</Label>
              <Input
                id="course_title"
                value={courseTitle}
                onChange={(e) => setCourseTitle(e.target.value)}
                placeholder="Data Structures"
              />
            </div>
            <div>
              <Label htmlFor="topic">Topic</Label>
              <Input
                id="topic"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="AVL Trees"
              />
            </div>
            <div>
              <Label htmlFor="faculty_question">Question</Label>
              <Input
                id="faculty_question"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="How to explain balancing quickly?"
              />
            </div>
          </div>

          <RequirePermission permission={PERMISSIONS.FACULTY_COPILOT_WRITE}>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={isBusy || !facultyId || !courseTitle || !topic}
                onClick={() =>
                  lessonPlan.mutate({
                    faculty_id: facultyId,
                    course_title: courseTitle,
                    topic,
                    duration_minutes: 90,
                  })
                }
              >
                Generate Lesson Plan
              </Button>
              <Button
                variant="outline"
                disabled={isBusy || !facultyId || !courseTitle || !topic}
                onClick={() =>
                  materialPack.mutate({
                    faculty_id: facultyId,
                    course_title: courseTitle,
                    topic,
                    material_type: "slides",
                  })
                }
              >
                Generate Materials
              </Button>
              <Button
                variant="secondary"
                disabled={isBusy || !facultyId || !question}
                onClick={() =>
                  qna.mutate({
                    faculty_id: facultyId,
                    course_title: courseTitle || undefined,
                    question,
                  })
                }
              >
                Ask Q&A
              </Button>
            </div>
          </RequirePermission>
        </div>

        <div className="rounded-lg border bg-card p-6 space-y-2">
          <h2 className="text-lg font-semibold">Last Answer</h2>
          {lastAnswer ? (
            <>
              <p className="text-sm text-muted-foreground">{lastAnswer.question}</p>
              <p className="text-sm">{lastAnswer.summary}</p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">No answer yet.</p>
          )}
        </div>
      </div>
    </RequirePermission>
  );
}
