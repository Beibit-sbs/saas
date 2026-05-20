'use client';

import React, { useState } from 'react';
import {
  useEscalationPolicies,
  useCreateEscalationPolicy,
  useUpdateEscalationPolicy,
  useArchiveEscalationPolicy,
} from '../hooks';
import { AssignmentPriority, EscalateToRole } from '../types';
import type {
  RectorAssignmentEscalationPolicy,
  EscalationPolicyCreatePayload,
} from '../types';
import { LoadingState, ErrorState } from '@/shared/ui/page-states';

// ---------------------------------------------------------------------------
// Form
// ---------------------------------------------------------------------------

interface FormState {
  assignment_priority: AssignmentPriority;
  escalation_level: string;
  escalate_to_role: EscalateToRole;
  escalate_after_hours: string;
  require_manual_confirmation: boolean;
}

const EMPTY_FORM: FormState = {
  assignment_priority: AssignmentPriority.NORMAL,
  escalation_level: '1',
  escalate_to_role: EscalateToRole.CONTROLLER,
  escalate_after_hours: '48',
  require_manual_confirmation: true, // MUST default to true
};

function policyToForm(p: RectorAssignmentEscalationPolicy): FormState {
  return {
    assignment_priority: p.assignment_priority as AssignmentPriority,
    escalation_level: String(p.escalation_level),
    escalate_to_role: p.escalate_to_role as EscalateToRole,
    escalate_after_hours: String(p.escalate_after_hours),
    require_manual_confirmation: p.require_manual_confirmation,
  };
}

function validate(f: FormState): string[] {
  const errors: string[] = [];
  const level = Number(f.escalation_level);
  if (isNaN(level) || level < 1 || level > 4)
    errors.push('Escalation level must be between 1 and 4.');
  const hours = Number(f.escalate_after_hours);
  if (isNaN(hours) || hours < 0)
    errors.push('Escalate after hours must be ≥ 0.');
  return errors;
}

interface EscalationPolicyFormProps {
  policy?: RectorAssignmentEscalationPolicy;
  onClose: () => void;
}

function EscalationPolicyForm({ policy, onClose }: EscalationPolicyFormProps) {
  const [form, setForm] = useState<FormState>(policy ? policyToForm(policy) : EMPTY_FORM);
  const [errors, setErrors] = useState<string[]>([]);
  const createMut = useCreateEscalationPolicy();
  const updateMut = useUpdateEscalationPolicy(policy?.id ?? 0);

  function update<K extends keyof FormState>(field: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate(form);
    if (errs.length > 0) { setErrors(errs); return; }
    setErrors([]);

    const payload: EscalationPolicyCreatePayload = {
      assignment_priority: form.assignment_priority,
      escalation_level: Number(form.escalation_level),
      escalate_to_role: form.escalate_to_role,
      escalate_after_hours: Number(form.escalate_after_hours),
      require_manual_confirmation: form.require_manual_confirmation,
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
      data-testid="escalation-policy-form-modal"
    >
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 className="text-lg font-semibold mb-4">
          {policy ? 'Edit Escalation Policy' : 'Create Escalation Policy'}
        </h2>

        {errors.length > 0 && (
          <div className="mb-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {errors.map((e) => <p key={e}>{e}</p>)}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Assignment Priority *</label>
              <select
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.assignment_priority}
                onChange={(e) => update('assignment_priority', e.target.value as AssignmentPriority)}
                data-testid="ep-priority-select"
              >
                {Object.values(AssignmentPriority).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Level (1–4) *</label>
              <input
                type="number"
                min={1}
                max={4}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.escalation_level}
                onChange={(e) => update('escalation_level', e.target.value)}
                data-testid="ep-level-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Escalate To *</label>
              <select
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.escalate_to_role}
                onChange={(e) => update('escalate_to_role', e.target.value as EscalateToRole)}
                data-testid="ep-role-select"
              >
                {Object.values(EscalateToRole).map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">After (hours) *</label>
              <input
                type="number"
                min={0}
                className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                value={form.escalate_after_hours}
                onChange={(e) => update('escalate_after_hours', e.target.value)}
                data-testid="ep-after-hours-input"
              />
            </div>
          </div>

          {/* require_manual_confirmation — MUST default to true */}
          <div className="flex items-start gap-3 rounded border border-amber-200 bg-amber-50 p-3">
            <input
              id="ep-manual-confirm"
              type="checkbox"
              checked={form.require_manual_confirmation}
              onChange={(e) => update('require_manual_confirmation', e.target.checked)}
              className="mt-0.5 h-4 w-4"
              data-testid="ep-manual-confirm-checkbox"
            />
            <div>
              <label htmlFor="ep-manual-confirm" className="text-sm font-medium text-gray-800">
                Require manual confirmation before escalation
              </label>
              <p className="text-xs text-gray-600 mt-0.5">
                Escalation will not be sent automatically. A reviewer must confirm.
                Manual confirmation required.
              </p>
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
              data-testid="ep-submit-btn"
            >
              {policy ? 'Update Escalation Policy' : 'Create Escalation Policy'}
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

export function EscalationPolicyManager() {
  const { data: policies, isLoading, isError } = useEscalationPolicies();
  const archiveMut = useArchiveEscalationPolicy();
  const [editPolicy, setEditPolicy] = useState<RectorAssignmentEscalationPolicy | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirmArchiveId, setConfirmArchiveId] = useState<number | null>(null);

  async function handleArchive() {
    if (confirmArchiveId == null) return;
    await archiveMut.mutateAsync(confirmArchiveId);
    setConfirmArchiveId(null);
  }

  if (isLoading) return <LoadingState message="Loading escalation policies..." />;
  if (isError) return <ErrorState message="Failed to load escalation policies." />;

  const active = policies?.filter((p) => !p.archived_at) ?? [];
  const archived = policies?.filter((p) => !!p.archived_at) ?? [];

  return (
    <div data-testid="escalation-policy-manager">
      {/* Required anti-fake notice */}
      <div
        className="mb-4 rounded border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-800"
        data-testid="escalation-manual-notice"
      >
        Manual confirmation required for all escalations. No autonomous escalation dispatch.
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Escalation Policies</h2>
        <button
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
          onClick={() => setCreating(true)}
          data-testid="create-escalation-policy-btn"
        >
          + Create Escalation Policy
        </button>
      </div>

      {active.length === 0 && archived.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-10 text-center" data-testid="ep-empty">
          <p className="text-gray-500 mb-3">No escalation policies configured.</p>
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
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Priority</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Level</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Escalate To</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">After (hrs)</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Manual Confirm</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Status</th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {[...active, ...archived].map((p) => (
                <tr
                  key={p.id}
                  className={p.archived_at ? 'opacity-50' : ''}
                  data-testid={`ep-row-${p.id}`}
                >
                  <td className="px-4 py-3 text-sm text-gray-800">{p.assignment_priority}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.escalation_level}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.escalate_to_role}</td>
                  <td className="px-4 py-3 text-sm text-gray-700">{p.escalate_after_hours}</td>
                  <td className="px-4 py-3 text-sm">
                    {p.require_manual_confirmation ? (
                      <span className="text-amber-700 font-medium" data-testid={`ep-manual-badge-${p.id}`}>
                        Manual confirmation required
                      </span>
                    ) : (
                      <span className="text-gray-400">—</span>
                    )}
                  </td>
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
                          data-testid={`ep-edit-${p.id}`}
                        >
                          Edit
                        </button>
                        <button
                          className="text-orange-600 hover:underline"
                          onClick={() => setConfirmArchiveId(p.id)}
                          data-testid={`ep-archive-${p.id}`}
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

      {creating && <EscalationPolicyForm onClose={() => setCreating(false)} />}
      {editPolicy && <EscalationPolicyForm policy={editPolicy} onClose={() => setEditPolicy(null)} />}

      {confirmArchiveId != null && (
        <div
          className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
          data-testid="ep-archive-confirm-modal"
        >
          <div className="bg-white rounded-xl shadow-xl p-6 max-w-sm w-full">
            <h3 className="text-base font-semibold mb-2">Archive Escalation Policy?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This escalation policy will be archived. No assignments will be automatically affected.
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
                data-testid="ep-archive-confirm-btn"
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
