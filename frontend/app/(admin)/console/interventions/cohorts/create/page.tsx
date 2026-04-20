'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useFinalizeCohortMutation } from '@/shared/hooks/useInterventionCohorts';
import type { CohortFinalizeRequest } from '@/shared/hooks/useInterventionCohorts';

const normalizeMutationError = (err: unknown): string => {
  if (err instanceof Error && err.message.trim()) {
    return err.message;
  }
  if (typeof err === 'string' && err.trim()) {
    return err;
  }
  return 'Failed to create cohort. Please try again.';
};

/**
 * Create Intervention Cohort Page
 *
 * Multi-step wizard for creating a new intervention cohort:
 * 1. Basic Info (name, outcome type, date range)
 * 2. Groups (cohort size, treatment/control split)
 * 3. Confirmation (review all fields)
 *
 * @route /console/interventions/cohorts/create
 */
export default function CreateCohortPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    playbookId: '',
    cohortName: '',
    outcomeType: '',
    analysisWindowStart: '',
    analysisWindowEnd: '',
    cohortSize: '',
    treatmentSize: '',
    controlSize: '',
  });

  const mutation = useFinalizeCohortMutation();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => {
      const updated = { ...prev, [name]: value };

      // Auto-calculate control size if treatment size changed
      if (name === 'treatmentSize' && updated.cohortSize) {
        const total = parseInt(updated.cohortSize, 10);
        const treatment = parseInt(value, 10);
        if (!isNaN(total) && !isNaN(treatment)) {
          updated.controlSize = String(total - treatment);
        }
      }

      // Auto-calculate treatment size if total changed
      if (name === 'cohortSize' && updated.treatmentSize) {
        const total = parseInt(value, 10);
        const treatment = parseInt(updated.treatmentSize, 10);
        if (!isNaN(total) && !isNaN(treatment)) {
          updated.controlSize = String(total - treatment);
        }
      }

      return updated;
    });
  };

  const validateStep = (currentStep: number): boolean => {
    setError(null);

    switch (currentStep) {
      case 0:
        if (!formData.playbookId) {
          setError('Please select a playbook');
          return false;
        }
        if (!formData.cohortName.trim()) {
          setError('Cohort name is required');
          return false;
        }
        if (!formData.analysisWindowStart) {
          setError('Start date is required');
          return false;
        }
        if (!formData.analysisWindowEnd) {
          setError('End date is required');
          return false;
        }
        if (new Date(formData.analysisWindowEnd) < new Date(formData.analysisWindowStart)) {
          setError('End date must be on or after start date');
          return false;
        }
        return true;

      case 1:
        const total = parseInt(formData.cohortSize, 10);
        const treatment = parseInt(formData.treatmentSize, 10);
        const control = parseInt(formData.controlSize, 10);

        if (isNaN(total) || total < 20) {
          setError('Cohort size must be at least 20');
          return false;
        }
        if (isNaN(treatment) || isNaN(control)) {
          setError('Treatment and control sizes must be numbers');
          return false;
        }
        if (treatment < 0 || control < 0) {
          setError('Treatment and control sizes cannot be negative');
          return false;
        }
        if (treatment > total) {
          setError('Treatment size cannot exceed total cohort size');
          return false;
        }
        if (treatment + control !== total) {
          setError('Treatment + Control must equal total cohort size');
          return false;
        }
        return true;

      case 2:
        return true; // Confirmation step, no validation needed

      default:
        return false;
    }
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep((s) => s + 1);
    }
  };

  const handlePrevious = () => {
    setStep((s) => Math.max(0, s - 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateStep(step)) {
      return;
    }

    const payload: CohortFinalizeRequest = {
      playbook_id: parseInt(formData.playbookId, 10),
      cohort_name: formData.cohortName.trim(),
      analysis_window_start: formData.analysisWindowStart,
      analysis_window_end: formData.analysisWindowEnd,
    };

    mutation.mutate(payload, {
      onSuccess: (data) => {
        // Redirect to detail page
        router.push(`/console/interventions/cohorts/${data.id}`);
      },
      onError: (err) => {
        setError(normalizeMutationError(err));
      },
    });
  };

  const steps = [
    { title: 'Basic Info', description: 'Cohort name and date range' },
    { title: 'Groups', description: 'Size and treatment/control split' },
    { title: 'Review', description: 'Confirm all details' },
  ];

  return (
    <div className="p-6 max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link href="/console/interventions/cohorts" className="text-blue-600 hover:text-blue-700 text-sm">
          ← Back to cohorts
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 mt-4">Create New Cohort</h1>
      </div>

      {/* Step indicator */}
      <div className="mb-8 flex gap-8">
        {steps.map((s, i) => (
          <div key={i} className="flex-1">
            <div
              className={`text-sm font-medium ${i <= step ? 'text-blue-600' : 'text-gray-500'}`}
            >
              Step {i + 1}
            </div>
            <p className={`text-xs mt-1 ${i <= step ? 'text-gray-700' : 'text-gray-400'}`}>
              {s.title}
            </p>
            <div
              className={`mt-2 h-2 rounded-full ${i <= step ? 'bg-blue-600' : 'bg-gray-200'}`}
            />
          </div>
        ))}
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-6 rounded-md bg-red-50 p-4 text-red-800 text-sm">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        {/* Step 0: Basic Info */}
        {step === 0 && (
          <div className="space-y-4">
            <div>
              <label htmlFor="playbookId" className="block text-sm font-medium text-gray-700 mb-2">
                Select Playbook
              </label>
              <select
                id="playbookId"
                name="playbookId"
                value={formData.playbookId}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
              >
                <option value="">-- Select a playbook --</option>
                <option value="1">Playbook 1</option>
                <option value="5">Playbook 5</option>
              </select>
            </div>

            <div>
              <label htmlFor="cohortName" className="block text-sm font-medium text-gray-700 mb-2">
                Cohort Name
              </label>
              <input
                id="cohortName"
                type="text"
                name="cohortName"
                value={formData.cohortName}
                onChange={handleInputChange}
                placeholder="e.g., Spring 2026 Cohort A"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="analysisWindowStart" className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  id="analysisWindowStart"
                  type="date"
                  name="analysisWindowStart"
                  value={formData.analysisWindowStart}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
                />
              </div>
              <div>
                <label htmlFor="analysisWindowEnd" className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  id="analysisWindowEnd"
                  type="date"
                  name="analysisWindowEnd"
                  value={formData.analysisWindowEnd}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 1: Groups */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label htmlFor="cohortSize" className="block text-sm font-medium text-gray-700 mb-2">
                Total Cohort Size (minimum 20)
              </label>
              <input
                id="cohortSize"
                type="number"
                name="cohortSize"
                value={formData.cohortSize}
                onChange={handleInputChange}
                min="20"
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="treatmentSize" className="block text-sm font-medium text-gray-700 mb-2">
                  Treatment Group Size
                </label>
                <input
                  id="treatmentSize"
                  type="number"
                  name="treatmentSize"
                  value={formData.treatmentSize}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500"
                />
                {formData.treatmentSize && formData.cohortSize && parseInt(formData.treatmentSize, 10) > parseInt(formData.cohortSize, 10) && (
                  <p className="text-xs text-red-600 mt-1">
                    Treatment size cannot exceed total cohort size
                  </p>
                )}
              </div>
              <div>
                <label htmlFor="controlSize" className="block text-sm font-medium text-gray-700 mb-2">
                  Control Group Size
                </label>
                <input
                  id="controlSize"
                  type="number"
                  name="controlSize"
                  value={formData.controlSize}
                  onChange={handleInputChange}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm bg-gray-50 text-gray-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Auto-calculated from total and treatment
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Review */}
        {step === 2 && (
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900">Review Cohort Details</h3>
            <div className="bg-gray-50 rounded-md p-4 space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Cohort Name:</span>
                <span className="font-medium text-gray-900">{formData.cohortName}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Analysis Window:</span>
                <span className="font-medium text-gray-900">
                  {formData.analysisWindowStart} to {formData.analysisWindowEnd}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Size:</span>
                <span className="font-medium text-gray-900">{formData.cohortSize} students</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Treatment / Control:</span>
                <span className="font-medium text-gray-900">
                  {formData.treatmentSize} / {formData.controlSize}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Buttons */}
        <div className="flex justify-between pt-6 border-t border-gray-200">
          <button
            type="button"
            onClick={handlePrevious}
            disabled={step === 0}
            className="inline-flex items-center justify-center rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {step < 2 ? (
            <button
              type="button"
              onClick={handleNext}
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending ? 'Creating...' : 'Create Cohort'}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
