import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PERMISSIONS } from '@/shared/config/permissions';
import {
  EXECUTIVE_CONTROL_TOWER_PERMISSIONS,
  EXECUTIVE_CONTROL_TOWER_READ_PERMISSIONS,
  EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS,
} from '@/modules/executive-control-tower/permissions';
import { ControlTowerNavTabs, PermissionDeniedPanel } from '@/modules/executive-control-tower/components';

vi.mock('@/shared/auth/context', () => ({
  useAdminAuth: () => ({
    hasPermission: (permission: string) => permission !== PERMISSIONS.EXECUTIVE_CONTROL_TOWER_METRIC_REGISTRY_READ,
  }),
}));

describe('Executive Control Tower permissions', () => {
  it('defines all frontend permission constants', () => {
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_READ).toBe('admin.executive_control_tower.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_SUMMARY_READ).toBe('admin.executive_control_tower.summary.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_ASSIGNMENTS_READ).toBe('admin.executive_control_tower.assignments.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_DOCUMENTS_READ).toBe('admin.executive_control_tower.documents.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_SLA_RISK_READ).toBe('admin.executive_control_tower.sla_risk.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_STRATEGY_READ).toBe('admin.executive_control_tower.strategy.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_AUDIT_READ).toBe('admin.executive_control_tower.audit.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_DEPARTMENT_READ).toBe('admin.executive_control_tower.department.read');
    expect(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_METRIC_REGISTRY_READ).toBe('admin.executive_control_tower.metric_registry.read');
  });

  it('exports read and section mappings', () => {
    expect(EXECUTIVE_CONTROL_TOWER_PERMISSIONS.READ).toBe(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_READ);
    expect(EXECUTIVE_CONTROL_TOWER_READ_PERMISSIONS).toHaveLength(9);
    expect(EXECUTIVE_CONTROL_TOWER_SECTION_PERMISSIONS.metricRegistry).toBe(PERMISSIONS.EXECUTIVE_CONTROL_TOWER_METRIC_REGISTRY_READ);
  });

  it('gates metric registry tab when permission is absent', () => {
    render(<ControlTowerNavTabs activePath="/console/executive-control-tower" />);
    expect(screen.queryByText(/metric registry/i)).toBeNull();
    expect(screen.getByText(/overview/i)).toBeTruthy();
  });

  it('renders permission denied placeholder', () => {
    render(<PermissionDeniedPanel message="Section is restricted" />);
    expect(screen.getByText(/section is restricted/i)).toBeTruthy();
  });
});