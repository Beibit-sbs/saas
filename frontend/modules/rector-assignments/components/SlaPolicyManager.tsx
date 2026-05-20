'use client';

import React, { useState } from 'react';
import {
  useSlaPolicies,
  useCreateSlaPolicy,
  useUpdateSlaPolicy,
  useArchiveSlaPolicy,
} from '../hooks';
import { AssignmentPriority } from '../types';
import type { RectorAssignmentSlaPolicy, SlaPolicyCreatePayload } from '../types';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

// ---------------------------------------------------------------------------
// Form
// ---------------------------------------------------------------------------

interface FormState {
  name: string;
  priority: AssignmentPriority;
  due_days: string;
  warning_before_hours: string;
  overdue_after_hours: string;
  escalation_after_hours: string;
}

const EMPTY_FORM: FormState = {
  name: '',
  priority: AssignmentPriority.NORMAL,
  due_days: '30',
  warning_before_hours: '48',
  overdue_after_hours: '24',
  escalation_after_hours: '72',
};

function policyToForm(p: RectorAssignmentSlaPolicy): FormState {
  return {
    name: p.name,
    priority: p.priority as AssignmentPriority,
    due_days: String(p.due_days),
    warning_before_hours: String(p.warning_before_hours),
    overdue_after_hours: String(p.overdue_after_hours),
    escalation_after_hours: String(p.escalation_after_hours),
  };
}

function validate(f: FormState): string[] {
  const errors: string[] = [];
  if (!f.name.trim()) errors.push('Name is required.');
  const dueDays = Number(f.due_days);
  const warnHours = Number(f.warning_before_hours);
  const overdueHours = Number(f.overdue_after_hours);
  const escalHours = Number(f.escalation_after_hours);
  if (isNaN(dueDays) || dueDays < 0) errors.push('Due days must be ≥ 0.');
  if (isNaN(warnHours) || warnHours < 0) errors.push('Warning hours must be ≥ 0.');
  if (isNaN(overdueHours) || overdueHours < 0) errors.push('Overdue hours must be ≥ 0.');
  if (!isNaN(escalHours) && !isNaN(overdueHours) && escalHours < overdueHours) {
    errors.push('Escalation hours must be ≥ overdue hours.');
  }
  return errors;
}

// ---------------------------------------------------------------------------
// Policy form modal
// ---------------------------------------------------------------------------

interface SlaPolicyFormProps {
  policy?: RectorAssignmentSlaPolicy;
  onClose: () => void;
}

function SlaPolicyForm({ policy, onClose }: SlaPolicyFormProps) {
  const [form, setForm] = useState<FormState>(policy ? policyToForm(policy) : EMPTY_FORM);
  const [errors, setErrors] = useState<string[]>([]);
  const createMut = useCreateSlaPolicy();
  const updateMut = useUpdateSlaPolicy(policy?.id ?? 0);

  function update(field: keyof FormState, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate(form);
    if (errs.length > 0) { setErrors(errs); return; }
    setErrors([]);

    const payload: SlaPolicyCreatePayload = {
      name: form.name.trim(),
      priority: form.priority,
      due_days: Number(form.due_days),
      warning_before_hours: Number(form.warning_before_hours),
      overdue_after_hours: Number(form.overdue_after_hours),
      escalation_after_hours: Number(form.escalation_after_hours),
    };

    if (policy) {
      await updateMut.mutateAsync(payload);
    } else {
      await createMut.mutateAsync(payload);
    }
    onClose();
  }

  return (
    <div
      className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
      data-testid="sla-policy-form-modal"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 className="text-lg font-semibold mb-4">
          {policy ? 'Edit SLA Policy' : 'Create SLA Policy'}
        </h2>

        {errors.length > 0 && (
          <div className="mb-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {errors.map((e) => <p key={e}>{e}</p>)}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              value={form.name}
              onChange={(e) => update('name', e.target.value)}
              data-testid="sla-name-input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority *</label>
            <select
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
              value={form.priority}
              onChange={(e) => update('priority', e.target.value)}
              data-testid="sla-priority-select"
            >
              {Object.values(AssignmentPriority).map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Days *</label>
              <input
                type="number"
                min={0}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.due_days}
                onChange={(e) => update('due_days', e.target.value)}
                data-testid="sla-due-days-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Warning Before (hrs) *</label>
              <input
                type="number"
                min={0}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.warning_before_hours}
                onChange={(e) => update('warning_before_hours', e.target.value)}
                data-testid="sla-warning-hours-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Overdue After (hrs) *</label>
              <input
                type="number"
                min={0}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.overdue_after_hours}
                onChange={(e) => update('overdue_after_hours', e.target.value)}
                data-testid="sla-overdue-hours-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Escalate After (hrs) *</label>
              <input
                type="number"
                min={0}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.escalation_after_hours}
                onChange={(e) => update('escalation_after_hours', e.target.value)}
                data-testid="sla-escalation-hours-input"
              />
            </div>
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              className="px-4 py-2 border border-gray-300 rounded text-sm hover:bg-gray-50"
              onClick={onClose}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 disabled:opacity-50"
              disabled={createMut.isPending || updateMut.isPending}
              data-testid="sla-submit-btn"
            >
              {policy ? 'Update SLA Policy' : 'Create SLA Policy'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main manager
// ---------------------------------------------------------------------------

export function SlaPolicyManager() {
  const { data: policies, isLoading, isError } = useSlaPolicies();
  const archiveMut = useArchiveSlaPolicy();
  const [editPolicy, setEditPolicy] = useState<RectorAssignmentSlaPolicy | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmArchiveId, setConfirmArchiveId] = useState<number | null>(null);

  async function handleArchive() {
    if (confirmArchiveId == null) return;
    await archiveMut.mutateAsync(confirmArchiveId);
    setConfirmArchiveId(null);
  }

  if (isLoading) return <LoadingState message="Loading SLA policies..." />;
  if (isError) return <ErrorState message="Failed to load SLA policies." />;

  const active = policies?.filter((p) => !p.archived_at) ?? [];
  const archived = policies?.filter((p) => !!p.archived_at) ?? [];

  return (
    <div data-testid="sla-policy-manager">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">SLA Policies</h2>
        <button
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          onClick={() => setCreating(true)}
          data-testid="create-sla-policy-btn"
        >
          + Create SLA Policy
        </button>
      </div>

      {active.length === 0 && archived.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-10 text-center" data-testid="sla-empty">
          <p className="text-gray-500 mb-3">No SLA policies configured.</p>
          <button
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded"
            onClick={() => setCreating(true)}
          >
            Create first policy
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-100">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Name</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Priority</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Due (days)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Warning (hrs)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Overdue (hrs)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Escalate (hrs)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Status</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[...active, ...archived].map((p) => (
                <tr
                  key={p.id}
                  className={p.archived_at ? 'opacity-50' : ''}
                  data-testid={`sla-row-${p.id}`}
                >
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{p.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.priority}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.due_days}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.warning_before_hours}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.overdue_after_hours}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.escalation_after_hours}</td>
                  <td className="px-4 py-3 text-sm">
                    {p.archived_at ? (
                      <span className="text-gray-400">Archived</span>
                    ) : (
                      <span className="text-green-700">Active</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm space-x-2">
                    {!p.archived_at && (
                      <>
                        <button
                          className="text-blue-600 hover:underline"
                          onClick={() => setEditPolicy(p)}
                          data-testid={`sla-edit-${p.id}`}
                        >
                          Edit
                        </button>
                        <button
                          className="text-orange-600 hover:underline"
                          onClick={() => setConfirmArchiveId(p.id)}
                          data-testid={`sla-archive-${p.id}`}
                        >
                          Archive
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      {creating && <SlaPolicyForm onClose={() => setCreating(false)} />}
      {editPolicy && <SlaPolicyForm policy={editPolicy} onClose={() => setEditPolicy(null)} />}

      {/* Archive confirmation */}
      {confirmArchiveId != null && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
          data-testid="sla-archive-confirm-modal"
        >
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-base font-semibold mb-2">Archive SLA Policy?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This policy will be archived and no longer applied to new assignments.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                className="px-4 py-2 border border-gray-300 rounded text-sm"
                onClick={() => setConfirmArchiveId(null)}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-orange-600 text-white rounded text-sm disabled:opacity-50"
                onClick={handleArchive}
                disabled={archiveMut.isPending}
                data-testid="sla-archive-confirm-btn"
              >
                Archive
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
