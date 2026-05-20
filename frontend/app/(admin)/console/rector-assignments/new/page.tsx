'use client';

/**
 * Create Rector Assignment Form
 * POST /api/admin/rector-assignments
 */

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  useCreateRectorAssignment,
  useRectorAssignmentTemplates,
} from '@/modules/rector-assignments/hooks';
import { AssignmentPriority, RecurrenceType } from '@/modules/rector-assignments/types';
import { PERMISSIONS } from '@/shared/config/permissions';
import { RequirePermission } from '@/shared/auth/permission-gate';
import { PageHeader } from '@/shared/ui/page-header';
import { LoadingState } from '@/shared/ui/page-states';
import { ApiRequestError } from '@/shared/api/client';

export default function NewRectorAssignmentPage() {
  const router = useRouter();
  const createMutation = useCreateRectorAssignment();
  const { data: templates, isLoading: isTemplatesLoading } = useRectorAssignmentTemplates();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<AssignmentPriority>(AssignmentPriority.NORMAL);
  const [dueDate, setDueDate] = useState('');
  const [recurrenceType, setRecurrenceType] = useState<RecurrenceType>(RecurrenceType.NONE);
  const [publishNow, setPublishNow] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [globalError, setGlobalError] = useState('');

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!title.trim()) {
      errors.title = 'Title is required.';
    } else if (title.trim().length < 3) {
      errors.title = 'Title must be at least 3 characters.';
    } else if (title.trim().length > 200) {
      errors.title = 'Title must be 200 characters or fewer.';
    }
    if (dueDate) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (new Date(dueDate) < today) {
        errors.dueDate = 'Due date cannot be in the past.';
      }
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGlobalError('');
    if (!validate()) return;

    try {
      const assignment = await createMutation.mutateAsync({
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
        due_date: dueDate || undefined,
        recurrence_type: recurrenceType,
        publish_now: publishNow,
      });
      router.push(`/console/rector-assignments/${assignment.id}`);
    } catch (err) {
      if (err instanceof ApiRequestError) {
        if (err.status === 422) {
          setGlobalError('Validation failed. Please check your inputs.');
        } else if (err.status === 403) {
          setGlobalError('You do not have permission to create assignments.');
        } else {
          setGlobalError(`Error: ${err.message}`);
        }
      } else {
        setGlobalError('An unexpected error occurred. Please try again.');
      }
    }
  }

  return (
    <RequirePermission permission={PERMISSIONS.RECTOR_ASSIGNMENTS_CREATE}>
      <div className="min-h-screen bg-gray-50">
        <PageHeader title="New Rector Assignment" />

        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow p-6">
            {globalError && (
              <div
                className="mb-4 p-3 rounded border border-red-200 bg-red-50 text-red-700 text-sm"
                role="alert"
                data-testid="global-error"
              >
                {globalError}
              </div>
            )}

            {isTemplatesLoading ? (
              <LoadingState message="Loading templates..." />
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5" data-testid="create-form" noValidate>
                {/* Template selector (optional) */}
                {templates && templates.length > 0 && (
                  <div>
                    <label htmlFor="template-select" className="block text-sm font-medium text-gray-700 mb-1">
                      Use Template (optional)
                    </label>
                    <select
                      id="template-select"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                      data-testid="template-select"
                      onChange={(e) => {
                        const t = templates.find((tmpl) => String(tmpl.id) === e.target.value);
                        if (t) {
                          if (t.default_priority) setPriority(t.default_priority);
                          if (t.default_recurrence_type) setRecurrenceType(t.default_recurrence_type);
                          if (t.template_body) setDescription(t.template_body);
                        }
                      }}
                    >
                      <option value="">— No template —</option>
                      {templates
                        .filter((t) => t.is_active)
                        .map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                    </select>
                  </div>
                )}

                {/* Title */}
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                    Title <span aria-hidden="true" className="text-red-500">*</span>
                  </label>
                  <input
                    id="title"
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md text-sm ${
                      fieldErrors.title ? 'border-red-400' : 'border-gray-300'
                    }`}
                    placeholder="Assignment title..."
                    data-testid="title-input"
                    required
                  />
                  {fieldErrors.title && (
                    <p className="mt-1 text-xs text-red-600" role="alert">{fieldErrors.title}</p>
                  )}
                </div>

                {/* Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    rows={4}
                    placeholder="Describe the assignment..."
                    data-testid="description-input"
                  />
                </div>

                {/* Priority */}
                <div>
                  <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                    Priority <span aria-hidden="true" className="text-red-500">*</span>
                  </label>
                  <select
                    id="priority"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as AssignmentPriority)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    data-testid="priority-select"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="NORMAL">Normal</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                {/* Due Date */}
                <div>
                  <label htmlFor="due-date" className="block text-sm font-medium text-gray-700 mb-1">
                    Due Date
                  </label>
                  <input
                    id="due-date"
                    type="date"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className={`w-full px-3 py-2 border rounded-md text-sm ${
                      fieldErrors.dueDate ? 'border-red-400' : 'border-gray-300'
                    }`}
                    data-testid="due-date-input"
                  />
                  {fieldErrors.dueDate && (
                    <p className="mt-1 text-xs text-red-600" role="alert">{fieldErrors.dueDate}</p>
                  )}
                </div>

                {/* Recurrence */}
                <div>
                  <label htmlFor="recurrence" className="block text-sm font-medium text-gray-700 mb-1">
                    Recurrence
                  </label>
                  <select
                    id="recurrence"
                    value={recurrenceType}
                    onChange={(e) => setRecurrenceType(e.target.value as RecurrenceType)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    data-testid="recurrence-select"
                  >
                    <option value="NONE">None (One-time)</option>
                    <option value="DAILY">Daily</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                    <option value="CUSTOM">Custom</option>
                  </select>
                </div>

                {/* Publish now toggle */}
                <div className="flex items-center gap-2">
                  <input
                    id="publish-now"
                    type="checkbox"
                    checked={publishNow}
                    onChange={(e) => setPublishNow(e.target.checked)}
                    className="h-4 w-4"
                    data-testid="publish-now-checkbox"
                  />
                  <label htmlFor="publish-now" className="text-sm text-gray-700">
                    Publish immediately (requires at least one assignee set after creation)
                  </label>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    data-testid="submit-btn"
                  >
                    {createMutation.isPending
                      ? 'Creating...'
                      : publishNow
                      ? 'Create & Publish'
                      : 'Save as Draft'}
                  </button>
                  <button
                    type="button"
                    onClick={() => router.back()}
                    className="px-4 py-2 text-sm font-medium text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
                    data-testid="cancel-btn"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </RequirePermission>
  );
}
