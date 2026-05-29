'use client';

import { Button } from '@/shared/ui/button';
import type { ActionDefinition } from '../types';

function isBlocked(action: ActionDefinition) {
  const missingPermission = Boolean(action.requiredPermission && action.hasPermission === false);
  return action.disabled || missingPermission;
}

function reason(action: ActionDefinition) {
  if (action.disabledReason) return action.disabledReason;
  if (action.requiredPermission && action.hasPermission === false) {
    return `Requires permission: ${action.requiredPermission}`;
  }
  return undefined;
}

export function PageActionBar({
  primaryAction,
  secondaryActions = [],
  customActions,
}: {
  primaryAction?: ActionDefinition;
  secondaryActions?: ActionDefinition[];
  customActions?: React.ReactNode;
}) {
  const renderAction = (action: ActionDefinition) => {
    const blocked = isBlocked(action);
    return (
      <Button
        key={action.id}
        variant={action.variant ?? 'outline'}
        onClick={action.onClick}
        disabled={blocked}
        title={reason(action)}
        data-testid={`ui-framework-action-${action.id}`}
      >
        {action.icon}
        <span>{action.label}</span>
      </Button>
    );
  };

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="ui-framework-page-action-bar">
      {secondaryActions.map(renderAction)}
      {primaryAction ? renderAction({ ...primaryAction, variant: primaryAction.variant ?? 'default' }) : null}
      {customActions}
    </div>
  );
}