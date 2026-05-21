import { beforeEach, describe, expect, it, vi } from 'vitest';

const mockApiGet = vi.fn();

vi.mock('@/shared/api/client', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
}));

describe('executiveControlTowerApi', () => {
  beforeEach(() => {
    mockApiGet.mockReset();
    mockApiGet.mockResolvedValue({});
  });

  it('uses GET only for the executive control tower summary endpoints', async () => {
    const { executiveControlTowerApi } = await import('@/modules/executive-control-tower/api');

    await executiveControlTowerApi.getExecutiveControlTowerSummary();
    await executiveControlTowerApi.getAssignmentExecutionSummary();
    await executiveControlTowerApi.getMetricRegistry();
    await executiveControlTowerApi.getExecutiveControlTowerHealth();

    expect(mockApiGet).toHaveBeenNthCalledWith(1, '/api/admin/executive-control-tower/summary');
    expect(mockApiGet).toHaveBeenNthCalledWith(2, '/api/admin/executive-control-tower/assignments');
    expect(mockApiGet).toHaveBeenNthCalledWith(3, '/api/admin/executive-control-tower/metric-registry');
    expect(mockApiGet).toHaveBeenNthCalledWith(4, '/api/admin/executive-control-tower/health');
  });

  it('calls each read-only section using the admin namespace', async () => {
    const { executiveControlTowerApi } = await import('@/modules/executive-control-tower/api');

    await executiveControlTowerApi.getDocumentWorkflowSummary();
    await executiveControlTowerApi.getDecreeWorkflowSummary();
    await executiveControlTowerApi.getCorrespondenceWorkflowSummary();
    await executiveControlTowerApi.getSlaRiskBottleneckSummary();
    await executiveControlTowerApi.getStrategyKpiSummary();
    await executiveControlTowerApi.getAuditComplianceSummary();
    await executiveControlTowerApi.getDepartmentPerformanceSummary();
    await executiveControlTowerApi.getMetricDetail('metric-1');

    const calledPaths = mockApiGet.mock.calls.map((call) => call[0]);
    expect(calledPaths).toEqual([
      '/api/admin/executive-control-tower/documents',
      '/api/admin/executive-control-tower/decrees',
      '/api/admin/executive-control-tower/correspondence',
      '/api/admin/executive-control-tower/sla-risk',
      '/api/admin/executive-control-tower/strategy-kpis',
      '/api/admin/executive-control-tower/audit-compliance',
      '/api/admin/executive-control-tower/department-performance',
      '/api/admin/executive-control-tower/metrics/metric-1',
    ]);
    expect(calledPaths.every((path) => typeof path === 'string' && path.startsWith('/api/admin/executive-control-tower'))).toBe(true);
  });

  it('exports no mutation methods', async () => {
    const { executiveControlTowerApi } = await import('@/modules/executive-control-tower/api');
    expect(Object.keys(executiveControlTowerApi).sort()).toEqual([
      'getAssignmentExecutionSummary',
      'getAuditComplianceSummary',
      'getCorrespondenceWorkflowSummary',
      'getDecreeWorkflowSummary',
      'getDepartmentPerformanceSummary',
      'getDocumentWorkflowSummary',
      'getExecutiveControlTowerHealth',
      'getExecutiveControlTowerSummary',
      'getMetricDetail',
      'getMetricRegistry',
      'getSlaRiskBottleneckSummary',
      'getStrategyKpiSummary',
    ]);
    expect(Object.keys(executiveControlTowerApi).some((key) => /create|update|delete|post|patch|put/i.test(key))).toBe(false);
  });
});