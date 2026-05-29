'use client';

import { Input } from '@/shared/ui/input';
import type { DateRangeValue } from '../types';

export function DateRangeFilter({
  value,
  onChange,
  disabled,
}: {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-center gap-2" data-testid="ui-framework-date-range-filter">
      <Input
        type="date"
        value={value.from}
        onChange={(event) => onChange({ ...value, from: event.target.value })}
        disabled={disabled}
        className="h-9 w-[170px]"
      />
      <Input
        type="date"
        value={value.to}
        onChange={(event) => onChange({ ...value, to: event.target.value })}
        disabled={disabled}
        className="h-9 w-[170px]"
      />
    </div>
  );
}