"use client";

import { Input } from "./input";
import { Button } from "./button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./select";
import { X } from "lucide-react";

interface FilterOption {
  label: string;
  value: string;
}

interface FilterField {
  key: string;
  label: string;
  type: "text" | "select";
  options?: FilterOption[];
  placeholder?: string;
}

interface FilterBarProps {
  fields: FilterField[];
  values: Record<string, string>;
  onChange: (key: string, value: string) => void;
  onReset?: () => void;
}

export function FilterBar({ fields, values, onChange, onReset }: FilterBarProps) {
  const hasValues = Object.values(values).some(Boolean);

  return (
    <div className="flex flex-wrap gap-2 items-center">
      {fields.map((f) =>
        f.type === "select" ? (
          <Select key={f.key} value={values[f.key] ?? ""} onValueChange={(v) => onChange(f.key, v === "all" ? "" : v)}>
            <SelectTrigger className="h-9 w-[160px]">
              <SelectValue placeholder={f.label} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All {f.label}</SelectItem>
              {f.options?.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        ) : (
          <Input
            key={f.key}
            placeholder={f.placeholder ?? `Filter ${f.label}…`}
            value={values[f.key] ?? ""}
            onChange={(e) => onChange(f.key, e.target.value)}
            className="h-9 w-[200px]"
          />
        ),
      )}
      {hasValues && onReset && (
        <Button variant="ghost" size="sm" onClick={onReset} className="h-9 px-2">
          <X className="h-4 w-4 mr-1" />
          Reset
        </Button>
      )}
    </div>
  );
}
