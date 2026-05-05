"use client";

import React, { useState } from "react";
import {
  useIntegrityCases,
  useCreateIntegrityCase,
  useUpdateIntegrityCaseStatus,
} from "@/modules/academic-integrity/hooks";
import {
  IntegrityCase,
  IntegrityCaseStatus,
  IntegrityCaseType,
  IntegrityCaseCreateRequest,
} from "@/modules/academic-integrity/types";
import { useLanguage } from "@/shared/providers/LanguageProvider";
import { Wave1KpiBar } from "@/modules/platform/kpi/wave1-kpi-bar";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CreateFormState {
  studentId: string;
  courseId: string;
  assignmentId: string;
  caseType: IntegrityCaseType;
  description: string;
  evidenceUrl: string;
  priority: "low" | "normal" | "high";
}

const INITIAL_FORM_STATE: CreateFormState = {
  studentId: "",
  courseId: "",
  assignmentId: "",
  caseType: IntegrityCaseType.PLAGIARISM,
  description: "",
  evidenceUrl: "",
  priority: "normal",
};

function getStatusLabel(status: IntegrityCaseStatus, lang: string): string {
  const labels: Record<IntegrityCaseStatus, Record<string, string>> = {
    [IntegrityCaseStatus.FLAGGED]: {
      ru: "Отмечено",
      en: "Flagged",
      kk: "Белгіленген",
    },
    [IntegrityCaseStatus.UNDER_REVIEW]: {
      ru: "На проверке",
      en: "Under Review",
      kk: "Тексеруде",
    },
    [IntegrityCaseStatus.RESOLVED]: {
      ru: "Разрешено",
      en: "Resolved",
      kk: "Шешілген",
    },
    [IntegrityCaseStatus.DISMISSED]: {
      ru: "Отклонено",
      en: "Dismissed",
      kk: "Жойылған",
    },
    [IntegrityCaseStatus.ESCALATED]: {
      ru: "Эскалировано",
      en: "Escalated",
      kk: "Көтерілген",
    },
  };
  return labels[status]?.[lang] || status;
}

function getTypeLabel(type: IntegrityCaseType, lang: string): string {
  const labels: Record<IntegrityCaseType, Record<string, string>> = {
    [IntegrityCaseType.PLAGIARISM]: { ru: "Плагиат", en: "Plagiarism", kk: "Плагиат" },
    [IntegrityCaseType.UNAUTHORIZED_COLLABORATION]: {
      ru: "Неавторизованное сотрудничество",
      en: "Unauthorized Collaboration",
      kk: "Рұқсатсыз ынамдастық",
    },
    [IntegrityCaseType.UNAUTHORIZED_AID]: {
      ru: "Неавторизованная помощь",
      en: "Unauthorized Aid",
      kk: "Рұқсатсыз көмек",
    },
    [IntegrityCaseType.FABRICATION]: {
      ru: "Фальсификация",
      en: "Fabrication",
      kk: "Жалпылау",
    },
    [IntegrityCaseType.CHEATING]: {
      ru: "Обман",
      en: "Cheating",
      kk: "Айла",
    },
  };
  return labels[type]?.[lang] || type;
}

function getStatusColor(status: IntegrityCaseStatus): string {
  switch (status) {
    case IntegrityCaseStatus.FLAGGED:
      return "bg-yellow-100 text-yellow-800";
    case IntegrityCaseStatus.UNDER_REVIEW:
      return "bg-blue-100 text-blue-800";
    case IntegrityCaseStatus.RESOLVED:
      return "bg-green-100 text-green-800";
    case IntegrityCaseStatus.DISMISSED:
      return "bg-gray-100 text-gray-800";
    case IntegrityCaseStatus.ESCALATED:
      return "bg-red-100 text-red-800";
  }
}

export default function AcademicIntegrityPage() {
  const { language } = useLanguage();
  const [page, setPage] = useState(1);
  const [filterStatus, setFilterStatus] = useState<string>("");
  const [formState, setFormState] = useState<CreateFormState>(INITIAL_FORM_STATE);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Queries
  const { data: casesData, isLoading } = useIntegrityCases(page, 20, undefined, filterStatus || undefined);
  const createMutation = useCreateIntegrityCase();
  const statusMutation = useUpdateIntegrityCaseStatus();

  // Handle create form submission
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload: IntegrityCaseCreateRequest = {
      student_id: formState.studentId,
      course_id: formState.courseId,
      assignment_id: formState.assignmentId || undefined,
      case_type: formState.caseType,
      description: formState.description,
      evidence_url: formState.evidenceUrl || undefined,
      priority: formState.priority,
    };

    try {
      await createMutation.mutateAsync(payload);
      setFormState(INITIAL_FORM_STATE);
      setCreateDialogOpen(false);
    } catch (error) {
      console.error("Failed to create case:", error);
    }
  };

  // Handle status update
  const handleStatusChange = async (caseId: string, newStatus: IntegrityCaseStatus) => {
    try {
      await statusMutation.mutateAsync({
        caseId,
        status: newStatus,
      });
    } catch (error) {
      console.error("Failed to update status:", error);
    }
  };

  return (
    <div className="space-y-6">
      <section data-testid="wave4-academic-integrity-kpi-section">
        <Wave1KpiBar
          metricKeys={[
            "academic_integrity_risk_count",
            "academic_integrity_review_cases_count",
            "academic_integrity_high_risk_count",
            "academic_integrity_cases_pending_review",
            "integrity_cases_open_count",
            "integrity_cases_escalated_count",
            "integrity_cases_resolved_count",
            "integrity_cases_evidence_requested_count",
            "integrity_case_resolution_sla_risk_count",
          ]}
          labels={{
            academic_integrity_risk_count: "Integrity Risk",
            academic_integrity_review_cases_count: "Review Cases",
            academic_integrity_high_risk_count: "High Risk",
            academic_integrity_cases_pending_review: "Pending Review",
            integrity_cases_open_count: "Cases Open",
            integrity_cases_escalated_count: "Cases Escalated",
            integrity_cases_resolved_count: "Cases Resolved",
            integrity_cases_evidence_requested_count: "Evidence Requested",
            integrity_case_resolution_sla_risk_count: "SLA Risk",
          }}
        />
      </section>
      <Card>
        <CardHeader>
          <CardTitle>{language === "ru" ? "Академическая честность" : "Academic Integrity"}</CardTitle>
          <CardDescription>
            {language === "ru"
              ? "Управление делами о нарушениях академической честности"
              : "Manage academic integrity violation cases"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder={language === "ru" ? "Фильтр по статусу..." : "Filter by status..."}
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value);
                setPage(1);
              }}
              className="w-64"
            />

            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button>{language === "ru" ? "Создать дело" : "Create Case"}</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>{language === "ru" ? "Новое дело" : "New Integrity Case"}</DialogTitle>
                  <DialogDescription>
                    {language === "ru"
                      ? "Заполните информацию о предполагаемом нарушении"
                      : "Fill in the details of the suspected violation"}
                  </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleCreateSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      {language === "ru" ? "ID студента" : "Student ID"}
                    </label>
                    <Input
                      value={formState.studentId}
                      onChange={(e) => setFormState({ ...formState, studentId: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      {language === "ru" ? "ID курса" : "Course ID"}
                    </label>
                    <Input
                      value={formState.courseId}
                      onChange={(e) => setFormState({ ...formState, courseId: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      {language === "ru" ? "Тип нарушения" : "Violation Type"}
                    </label>
                    <select
                      value={formState.caseType}
                      onChange={(e) =>
                        setFormState({
                          ...formState,
                          caseType: e.target.value as IntegrityCaseType,
                        })
                      }
                      className="w-full px-3 py-2 border rounded-md"
                    >
                      {Object.values(IntegrityCaseType).map((type) => (
                        <option key={type} value={type}>
                          {getTypeLabel(type, language)}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">
                      {language === "ru" ? "Описание" : "Description"}
                    </label>
                    <textarea
                      value={formState.description}
                      onChange={(e) => setFormState({ ...formState, description: e.target.value })}
                      required
                      className="w-full px-3 py-2 border rounded-md"
                      rows={4}
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button type="submit" disabled={createMutation.isPending}>
                      {language === "ru" ? "Создать" : "Create"}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setCreateDialogOpen(false)}
                    >
                      {language === "ru" ? "Отменить" : "Cancel"}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      {/* Cases Table */}
      {isLoading ? (
        <div>{language === "ru" ? "Загрузка..." : "Loading..."}</div>
      ) : !casesData?.cases.length ? (
        <div>{language === "ru" ? "Дел не найдено" : "No cases found"}</div>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{language === "ru" ? "Студент" : "Student"}</TableHead>
                <TableHead>{language === "ru" ? "Курс" : "Course"}</TableHead>
                <TableHead>{language === "ru" ? "Тип" : "Type"}</TableHead>
                <TableHead>{language === "ru" ? "Статус" : "Status"}</TableHead>
                <TableHead>{language === "ru" ? "Приоритет" : "Priority"}</TableHead>
                <TableHead>{language === "ru" ? "Действия" : "Actions"}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {casesData?.cases.map((caseItem: IntegrityCase) => (
                <TableRow key={caseItem.id}>
                  <TableCell>{caseItem.student_id}</TableCell>
                  <TableCell>{caseItem.course_id}</TableCell>
                  <TableCell>{getTypeLabel(caseItem.case_type as IntegrityCaseType, language)}</TableCell>
                  <TableCell>
                    <Badge className={getStatusColor(caseItem.status as IntegrityCaseStatus)}>
                      {getStatusLabel(caseItem.status as IntegrityCaseStatus, language)}
                    </Badge>
                  </TableCell>
                  <TableCell>{caseItem.priority}</TableCell>
                  <TableCell>
                    {caseItem.status === IntegrityCaseStatus.FLAGGED ? (
                      <Button
                        size="sm"
                        onClick={() =>
                          handleStatusChange(
                            caseItem.id,
                            IntegrityCaseStatus.UNDER_REVIEW
                          )
                        }
                        disabled={statusMutation.isPending}
                      >
                        {language === "ru" ? "Начать проверку" : "Start Review"}
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Pagination */}
      {casesData && casesData.total > 0 && (
        <div className="flex justify-between items-center">
          <div>
            {language === "ru"
              ? `Показано ${(page - 1) * 20 + 1}-${Math.min(page * 20, casesData.total)} из ${casesData.total}`
              : `Showing ${(page - 1) * 20 + 1}-${Math.min(page * 20, casesData.total)} of ${casesData.total}`}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
            >
              {language === "ru" ? "Назад" : "Previous"}
            </Button>
            <Button
              variant="outline"
              onClick={() => setPage(page + 1)}
              disabled={page * 20 >= casesData.total}
            >
              {language === "ru" ? "Дальше" : "Next"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
