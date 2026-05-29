'use client';

import { Input } from '@/shared/ui/input';

export function SearchInput({
  value,
  onChange,
  placeholder = 'Search',
  disabled,
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <Input
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
      disabled={disabled}
      className="h-9 w-[220px]"
      data-testid="ui-framework-search-input"
    />
  );
}