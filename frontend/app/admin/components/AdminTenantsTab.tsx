import { useState } from "react";

import type { InlineFeedback } from "../types";
import type { Tenant } from "../hooks/useAdminTenants";

type AdminTenantsTabProps = {
  tenants: Tenant[];
  loading: boolean;
  mutating: boolean;
  feedback: InlineFeedback | null;
  lastUpdated: string;
  onRefresh: () => Promise<void>;
  onCreateTenant: (payload: { slug: string; name: string; status: string }) => Promise<Tenant | null>;
  onUpdateTenant: (id: number, payload: { name?: string; status?: string }) => Promise<Tenant | null>;
  onDeleteTenant: (id: number) => Promise<boolean>;
};

const STATUS_OPTIONS = ["active", "inactive"];

const emptyForm = () => ({ slug: "", name: "", status: "active" });
const emptyEditForm = () => ({ name: "", status: "active" });

export function AdminTenantsTab({
  tenants,
  loading,
  mutating,
  feedback,
  lastUpdated,
  onRefresh,
  onCreateTenant,
  onUpdateTenant,
  onDeleteTenant,
}: AdminTenantsTabProps) {
  const [createForm, setCreateForm] = useState(emptyForm());
  const [editId, setEditId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState(emptyEditForm());

  const clearCreate = () => setCreateForm(emptyForm());

  const startEdit = (tenant: Tenant) => {
    setEditId(tenant.id);
    setEditForm({ name: tenant.name, status: tenant.status });
  };

  const cancelEdit = () => {
    setEditId(null);
    setEditForm(emptyEditForm());
  };

  const canCreate = createForm.slug.trim().length > 0 && createForm.name.trim().length > 0;

  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>Tenants</h2>
        <p className="subText">Last refresh: {lastUpdated}{loading ? " · Loading..." : ""}</p>
        {feedback ? (
          <p
            className={`inlineFeedback inlineFeedback${
              feedback.tone === "error"
                ? "Error"
                : feedback.tone === "success"
                  ? "Success"
                  : "Info"
            }`}
          >
            {feedback.message}
          </p>
        ) : null}

        <div className="rowButtons" style={{ marginTop: 12 }}>
          <button type="button" className="ghost" onClick={() => void onRefresh()} disabled={loading || mutating}>
            {loading ? "Loading..." : "Refresh"}
          </button>
          <span className="badge badgeInfo">Total: {tenants.length}</span>
          <span className="badge badgeOk">
            Active: {tenants.filter((t) => t.status === "active").length}
          </span>
        </div>
      </article>

      <article className="panelCard">
        <h2>Create Tenant</h2>
        <div className="formGrid compactFormGrid">
          <label style={{ display: "grid", gap: 4 }}>
            <span className="subText">Slug</span>
            <input
              type="text"
              value={createForm.slug}
              onChange={(e) => setCreateForm((f) => ({ ...f, slug: e.target.value }))}
              placeholder="e.g. acme-corp"
            />
          </label>
          <label style={{ display: "grid", gap: 4 }}>
            <span className="subText">Name</span>
            <input
              type="text"
              value={createForm.name}
              onChange={(e) => setCreateForm((f) => ({ ...f, name: e.target.value }))}
              placeholder="Organization name"
            />
          </label>
          <label style={{ display: "grid", gap: 4 }}>
            <span className="subText">Status</span>
            <select
              value={createForm.status}
              onChange={(e) => setCreateForm((f) => ({ ...f, status: e.target.value }))}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>

        <div className="rowButtons" style={{ marginTop: 12 }}>
          <button
            type="button"
            className="primary"
            disabled={!canCreate || mutating}
            onClick={async () => {
              const created = await onCreateTenant(createForm);
              if (created) {
                clearCreate();
              }
            }}
          >
            {mutating ? "Saving..." : "Create tenant"}
          </button>
          <button type="button" className="ghost" onClick={clearCreate} disabled={mutating}>
            Clear
          </button>
        </div>
      </article>

      <article className="panelCard" style={{ gridColumn: "1 / -1" }}>
        <h2>Tenants Table</h2>
        {tenants.length === 0 ? (
          <p className="subText">No tenants yet.</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>id</th>
                  <th>slug</th>
                  <th>name</th>
                  <th>status</th>
                  <th>created_at</th>
                  <th>updated_at</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((tenant) => (
                  <tr key={tenant.id}>
                    <td>{tenant.id}</td>
                    <td>{tenant.slug}</td>
                    <td>
                      {editId === tenant.id ? (
                        <input
                          type="text"
                          value={editForm.name}
                          onChange={(e) => setEditForm((f) => ({ ...f, name: e.target.value }))}
                          style={{ width: "100%" }}
                        />
                      ) : (
                        tenant.name
                      )}
                    </td>
                    <td>
                      {editId === tenant.id ? (
                        <select
                          value={editForm.status}
                          onChange={(e) => setEditForm((f) => ({ ...f, status: e.target.value }))}
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>{s}</option>
                          ))}
                        </select>
                      ) : (
                        <span className={`badge ${tenant.status === "active" ? "badgeOk" : "badgeWarn"}`}>
                          {tenant.status}
                        </span>
                      )}
                    </td>
                    <td>{tenant.created_at}</td>
                    <td>{tenant.updated_at}</td>
                    <td>
                      <div className="rowButtons">
                        {editId === tenant.id ? (
                          <>
                            <button
                              type="button"
                              className="primary"
                              disabled={mutating}
                              onClick={async () => {
                                const updated = await onUpdateTenant(tenant.id, editForm);
                                if (updated) {
                                  cancelEdit();
                                }
                              }}
                            >
                              {mutating ? "Saving..." : "Save"}
                            </button>
                            <button type="button" className="ghost" onClick={cancelEdit} disabled={mutating}>
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button type="button" className="ghost" onClick={() => startEdit(tenant)}>
                              Edit
                            </button>
                            <button
                              type="button"
                              className="ghost danger"
                              disabled={mutating || tenant.id === 1}
                              title={tenant.id === 1 ? "Default tenant cannot be deactivated" : "Deactivate"}
                              onClick={() => void onDeleteTenant(tenant.id)}
                            >
                              Deactivate
                            </button>
                          </>
                        )}
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
