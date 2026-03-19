import { useMemo, useState } from "react";

import type { InlineFeedback } from "../types";
import type { UniversityEntity } from "../hooks/useAdminUniversity";

type FieldConfig = {
  name: string;
  label: string;
  numeric?: boolean;
};

type EntityConfig = {
  label: string;
  keyPrefix: string;
  fields: FieldConfig[];
};

type AdminUniversityTabProps = {
  activeEntity: UniversityEntity;
  onEntityChange: (entity: UniversityEntity) => void;
  itemsByEntity: Record<UniversityEntity, Array<Record<string, unknown>>>;
  loading: boolean;
  mutating: boolean;
  feedback: InlineFeedback | null;
  lastUpdated: string;
  onRefresh: (entity?: UniversityEntity) => Promise<void>;
  onCreateItem: (entity: UniversityEntity, payload: Record<string, unknown>) => Promise<Record<string, unknown> | null>;
  onUpdateItem: (entity: UniversityEntity, id: number, payload: Record<string, unknown>) => Promise<Record<string, unknown> | null>;
  onDeleteItem: (entity: UniversityEntity, id: number) => Promise<boolean>;
};

const ENTITY_CONFIGS: Record<UniversityEntity, EntityConfig> = {
  students: {
    label: "Students",
    keyPrefix: "student",
    fields: [
      { name: "student_id", label: "Student ID" },
      { name: "first_name", label: "First name" },
      { name: "last_name", label: "Last name" },
      { name: "email", label: "Email" },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
  faculty: {
    label: "Faculty",
    keyPrefix: "faculty",
    fields: [
      { name: "faculty_id", label: "Faculty ID" },
      { name: "first_name", label: "First name" },
      { name: "last_name", label: "Last name" },
      { name: "department", label: "Department" },
      { name: "email", label: "Email" },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
  programs: {
    label: "Programs",
    keyPrefix: "program",
    fields: [
      { name: "program_code", label: "Program code" },
      { name: "title", label: "Title" },
      { name: "degree_type", label: "Degree type" },
      { name: "faculty", label: "Faculty" },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
  courses: {
    label: "Courses",
    keyPrefix: "course",
    fields: [
      { name: "course_code", label: "Course code" },
      { name: "title", label: "Title" },
      { name: "credits", label: "Credits", numeric: true },
      { name: "program_id", label: "Program ID", numeric: true },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
  enrollments: {
    label: "Enrollments",
    keyPrefix: "enrollment",
    fields: [
      { name: "student_id", label: "Student row ID", numeric: true },
      { name: "course_id", label: "Course row ID", numeric: true },
      { name: "semester", label: "Semester" },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
  records: {
    label: "Records",
    keyPrefix: "record",
    fields: [
      { name: "student_id", label: "Student row ID", numeric: true },
      { name: "course_id", label: "Course row ID", numeric: true },
      { name: "grade", label: "Grade" },
      { name: "semester", label: "Semester" },
      { name: "status", label: "Status" },
      { name: "tenant_id", label: "Tenant ID" },
    ],
  },
};

const UNIVERSITY_ENTITIES: UniversityEntity[] = ["students", "faculty", "programs", "courses", "enrollments", "records"];

const emptyFormByEntity = (): Record<UniversityEntity, Record<string, string>> => {
  const forms = {
    students: {},
    faculty: {},
    programs: {},
    courses: {},
    enrollments: {},
    records: {},
  } as Record<UniversityEntity, Record<string, string>>;

  for (const entity of UNIVERSITY_ENTITIES) {
    for (const field of ENTITY_CONFIGS[entity].fields) {
      forms[entity][field.name] = "";
    }
  }

  return forms;
};

export function AdminUniversityTab({
  activeEntity,
  onEntityChange,
  itemsByEntity,
  loading,
  mutating,
  feedback,
  lastUpdated,
  onRefresh,
  onCreateItem,
  onUpdateItem,
  onDeleteItem,
}: AdminUniversityTabProps) {
  const [forms, setForms] = useState<Record<UniversityEntity, Record<string, string>>>(emptyFormByEntity);
  const [editId, setEditId] = useState<number | null>(null);

  const config = ENTITY_CONFIGS[activeEntity];
  const items = itemsByEntity[activeEntity] || [];

  const visibleColumns = useMemo(() => {
    const base = ["id", ...config.fields.map((field) => field.name)];
    if (activeEntity === "students") {
      base.push("created_at");
    }
    return base;
  }, [activeEntity, config.fields]);

  const currentForm = forms[activeEntity] || {};

  const updateFormValue = (fieldName: string, value: string) => {
    setForms((current) => ({
      ...current,
      [activeEntity]: {
        ...current[activeEntity],
        [fieldName]: value,
      },
    }));
  };

  const clearForm = () => {
    setForms((current) => {
      const next = { ...current };
      next[activeEntity] = {};
      for (const field of config.fields) {
        next[activeEntity][field.name] = "";
      }
      return next;
    });
    setEditId(null);
  };

  const buildPayload = () => {
    const payload: Record<string, unknown> = {};
    for (const field of config.fields) {
      const raw = (currentForm[field.name] || "").trim();
      if (!raw) {
        payload[field.name] = field.name === "tenant_id" ? null : "";
        continue;
      }
      payload[field.name] = field.numeric ? Number(raw) : raw;
    }
    return payload;
  };

  const startEdit = (item: Record<string, unknown>) => {
    const next: Record<string, string> = {};
    for (const field of config.fields) {
      const value = item[field.name];
      next[field.name] = value === null || value === undefined ? "" : String(value);
    }
    setForms((current) => ({ ...current, [activeEntity]: next }));
    setEditId(Number(item.id));
  };

  const canSubmit = config.fields.every((field) => {
    if (field.name === "tenant_id") {
      return true;
    }
    return (currentForm[field.name] || "").trim().length > 0;
  });

  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>University Core</h2>
        <p className="subText">Last refresh: {lastUpdated}{loading ? " · Loading..." : ""}</p>
        {feedback ? (
          <p className={`inlineFeedback inlineFeedback${feedback.tone === "error" ? "Error" : feedback.tone === "success" ? "Success" : "Info"}`}>
            {feedback.message}
          </p>
        ) : null}

        <div className="badgeRow" style={{ marginTop: 10 }}>
          {UNIVERSITY_ENTITIES.map((entity) => (
            <button
              key={entity}
              type="button"
              className={`badge ${activeEntity === entity ? "badgeOk" : "badgeInfo"}`}
              onClick={() => {
                onEntityChange(entity);
                setEditId(null);
              }}
            >
              {ENTITY_CONFIGS[entity].label}
            </button>
          ))}
        </div>

        <div className="rowButtons" style={{ marginTop: 12 }}>
          <button type="button" className="ghost" onClick={() => void onRefresh(activeEntity)} disabled={loading || mutating}>
            {loading ? "Loading..." : "Refresh"}
          </button>
          <span className="badge badgeInfo">Rows: {items.length}</span>
          <span className="badge badgeWarn">Mode: {editId ? "Update" : "Create"}</span>
        </div>
      </article>

      <article className="panelCard">
        <h2>{config.label} CRUD</h2>
        <div className="formGrid compactFormGrid">
          {config.fields.map((field) => (
            <label key={field.name} style={{ display: "grid", gap: 4 }}>
              <span className="subText">{field.label}</span>
              <input
                type={field.numeric ? "number" : "text"}
                value={currentForm[field.name] || ""}
                onChange={(event) => updateFormValue(field.name, event.target.value)}
                placeholder={field.label}
              />
            </label>
          ))}
        </div>

        <div className="rowButtons" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="primary"
            disabled={!canSubmit || mutating}
            onClick={async () => {
              if (!canSubmit) {
                return;
              }
              const payload = buildPayload();
              if (editId) {
                const updated = await onUpdateItem(activeEntity, editId, payload);
                if (updated) {
                  clearForm();
                }
                return;
              }
              const created = await onCreateItem(activeEntity, payload);
              if (created) {
                clearForm();
              }
            }}
          >
            {mutating ? "Saving..." : editId ? `Update ${config.keyPrefix}` : `Create ${config.keyPrefix}`}
          </button>
          <button type="button" className="ghost" disabled={mutating} onClick={clearForm}>
            Clear
          </button>
        </div>
      </article>

      <article className="panelCard" style={{ gridColumn: "1 / -1" }}>
        <h2>{config.label} Table</h2>
        {items.length === 0 ? (
          <p className="subText">No rows yet.</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  {visibleColumns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={`${activeEntity}-${String(item.id)}`}>
                    {visibleColumns.map((column) => (
                      <td key={column}>{String(item[column] ?? "-")}</td>
                    ))}
                    <td>
                      <div className="rowButtons">
                        <button type="button" className="ghost" onClick={() => startEdit(item)}>Edit</button>
                        <button
                          type="button"
                          className="ghost danger"
                          onClick={() => void onDeleteItem(activeEntity, Number(item.id))}
                          disabled={mutating}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </div>
  );
}
