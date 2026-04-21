"use client";

import { useState } from "react";

import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/ui/dialog";
import { Input } from "@/shared/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import {
  useAccreditation,
  useCreateAccreditation,
  useUpdateAccreditationStatus,
} from "@/modules/accreditation/hooks";
import type {
  AccreditationCreatePayload,
  AccreditationRecord,
  AccreditationStandardType,
  AccreditationStatus,
} from "@/modules/accreditation/types";

type FormState = AccreditationCreatePayload;

const INITIAL_FORM_STATE: FormState = {
  standard_code: "",
  standard_type: "institutional",
  title: "",
  owner_department: "",
  review_cycle_year: 2026,
  due_date: null,
  evidence_summary: "",
  risk_level: "medium",
};

function getStatusLabel(status: AccreditationStatus): string {
  const labels: Record<AccreditationStatus, string> = {
    draft: "Draft",
    evidence_requested: "Evidence Requested",
    evidence_collected: "Evidence Collected",
    under_review: "Under Review",
    compliant: "Compliant",
    remediation_required: "Remediation Required",
  };
  return labels[status] ?? status;
}

function getTypeLabel(type: AccreditationStandardType): string {
  const labels: Record<AccreditationStandardType, string> = {
    institutional: "Institutional",
    programmatic: "Programmatic",
    curriculum: "Curriculum",
    faculty_qualifications: "Faculty Qualifications",
    learning_outcomes: "Learning Outcomes",
  };
  return labels[type] ?? type;
}

function getStatusColor(status: AccreditationStatus): string {
  switch (status) {
    case "draft":
      return "bg-slate-100 text-slate-800";
    case "evidence_requested":
      return "bg-amber-100 text-amber-800";
    case "evidence_collected":
      return "bg-sky-100 text-sky-800";
    case "under_review":
      return "bg-blue-100 text-blue-800";
    case "compliant":
      return "bg-green-100 text-green-800";
    case "remediation_required":
      return "bg-red-100 text-red-800";
  }
}

export default function AccreditationCompliancePage() {
  const [statusFilter, setStatusFilter] = useState<AccreditationStatus | undefined>(undefined);
  const [typeFilter, setTypeFilter] = useState<AccreditationStandardType | undefined>(undefined);
  const [formState, setFormState] = useState<FormState>(INITIAL_FORM_STATE);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading } = useAccreditation(statusFilter, typeFilter);
  const createMutation = useCreateAccreditation();
  const updateStatusMutation = useUpdateAccreditationStatus();

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    await createMutation.mutateAsync({
      ...formState,
      evidence_summary: formState.evidence_summary || null,
      due_date: formState.due_date || null,
    });
    setFormState(INITIAL_FORM_STATE);
    setDialogOpen(false);
  };

  const handlePromote = async (item: AccreditationRecord) => {
    const nextStatus: AccreditationStatus =
      item.status === "draft"
        ? "evidence_requested"
        : item.status === "evidence_requested"
          ? "evidence_collected"
          : item.status === "evidence_collected"
            ? "under_review"
            : item.status === "under_review"
              ? "compliant"
              : item.status;

    if (nextStatus === item.status) {
      return;
    }

    await updateStatusMutation.mutateAsync({
      recordId: item.id,
      payload: { status: nextStatus },
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Accreditation Compliance</CardTitle>
          <CardDescription>
            Track accreditation standards, evidence readiness, review state, and remediation follow-up.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Input
              placeholder="Filter by status"
              value={statusFilter ?? ""}
              onChange={(event) =>
                setStatusFilter((event.target.value || undefined) as AccreditationStatus | undefined)
              }
              className="w-56"
            />
            <Input
              placeholder="Filter by standard type"
              value={typeFilter ?? ""}
              onChange={(event) =>
                setTypeFilter((event.target.value || undefined) as AccreditationStandardType | undefined)
              }
              className="w-56"
            />
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button>Create Standard Record</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>New Accreditation Record</DialogTitle>
                  <DialogDescription>
                    Register a new standard, its owner, and the current evidence posture.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreate} className="space-y-4">
                  <Input
                    placeholder="Standard code"
                    value={formState.standard_code}
                    onChange={(event) => setFormState((prev) => ({ ...prev, standard_code: event.target.value }))}
                    required
                  />
                  <Input
                    placeholder="Title"
                    value={formState.title}
                    onChange={(event) => setFormState((prev) => ({ ...prev, title: event.target.value }))}
                    required
                  />
                  <Input
                    placeholder="Owner department"
                    value={formState.owner_department}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, owner_department: event.target.value }))
                    }
                    required
                  />
                  <Input
                    placeholder="Standard type"
                    value={formState.standard_type}
                    onChange={(event) =>
                      setFormState((prev) => ({
                        ...prev,
                        standard_type: event.target.value as AccreditationStandardType,
                      }))
                    }
                    required
                  />
                  <Input
                    placeholder="Review cycle year"
                    type="number"
                    value={formState.review_cycle_year}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, review_cycle_year: Number(event.target.value) }))
                    }
                    required
                  />
                  <Input
                    placeholder="Evidence summary"
                    value={formState.evidence_summary ?? ""}
                    onChange={(event) =>
                      setFormState((prev) => ({ ...prev, evidence_summary: event.target.value }))
                    }
                  />
                  <div className="flex gap-2">
                    <Button type="submit" disabled={createMutation.isPending}>Create</Button>
                    <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                      Cancel
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <div>Loading accreditation records...</div>
      ) : !data?.items.length ? (
        <div>No accreditation records found.</div>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Owner</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.standard_code}</TableCell>
                  <TableCell>{item.title}</TableCell>
                  <TableCell>{getTypeLabel(item.standard_type)}</TableCell>
                  <TableCell>{item.owner_department}</TableCell>
                  <TableCell>
                    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${getStatusColor(item.status)}`}>
                      {getStatusLabel(item.status)}
                    </span>
                  </TableCell>
                  <TableCell className="uppercase">{item.risk_level}</TableCell>
                  <TableCell>
                    <Button variant="outline" size="sm" onClick={() => void handlePromote(item)}>
                      Advance Status
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
