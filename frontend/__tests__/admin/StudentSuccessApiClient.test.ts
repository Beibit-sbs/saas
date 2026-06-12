import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}));

describe('studentSuccessApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiGet.mockResolvedValue({});
  });

  it('uses the student success runtime shell API endpoint', async () => {
    const { studentSuccessApi } = await import('@/modules/student-success/api');
    await studentSuccessApi.getRuntimeShell();

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/student-success/runtime-shell');
  });

  it('uses the student registry runtime API endpoint', async () => {
    const { studentSuccessApi } = await import('@/modules/student-success/api');
    await studentSuccessApi.getStudentRegistryRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/student-success/student-registry');
  });

  it('uses the student retention runtime API endpoint', async () => {
    const { studentSuccessApi } = await import('@/modules/student-success/api');
    await studentSuccessApi.getStudentRetentionRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/student-success/student-retention');
  });

  it('uses the student academic risk runtime API endpoint', async () => {
    const { studentSuccessApi } = await import('@/modules/student-success/api');
    await studentSuccessApi.getStudentAcademicRiskRuntime();

    expect(mockApiGet).toHaveBeenCalledWith('/api/v1/student-success/academic-risk');
  });
});
