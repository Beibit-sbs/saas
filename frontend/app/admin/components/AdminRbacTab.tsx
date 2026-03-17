import type { AdminCopy, InlineFeedback, RbacRoleEntry, TxFn } from "../types";

type RbacAssignmentRow = {
  user_id: string;
  role: string;
};

type AdminRbacTabProps = {
  l: AdminCopy;
  tx: TxFn;
  rbacFeedback: InlineFeedback | null;
  newRoleName: string;
  newRolePermissions: string;
  rbacRoleSaveBusy: boolean;
  rbacRolesBusy: boolean;
  rbacRoles: RbacRoleEntry[];
  assignUserId: string;
  assignRoleName: string;
  rbacAssignBusy: boolean;
  rbacAssignmentsBusy: boolean;
  assignmentUserFilter: string;
  assignmentRoleFilter: string;
  rbacAssignmentRows: RbacAssignmentRow[];
  rbacAssignmentsCount: number;
  rbacFilterBadges: string[];
  rbacRevokeBusyKey: string;
  onNewRoleNameChange: (value: string) => void;
  onNewRolePermissionsChange: (value: string) => void;
  onSaveRbacRole: () => void | Promise<void>;
  onLoadRbacRoles: () => void | Promise<void>;
  onAssignUserIdChange: (value: string) => void;
  onAssignRoleNameChange: (value: string) => void;
  onAssignRbacRole: () => void | Promise<void>;
  onLoadRbacAssignments: () => void | Promise<void>;
  onClearRbacFilters: () => void;
  onAssignmentUserFilterChange: (value: string) => void;
  onAssignmentRoleFilterChange: (value: string) => void;
  onRevokeRbacRole: (userId: string, role: string) => void | Promise<void>;
};

export function AdminRbacTab({
  l,
  tx,
  rbacFeedback,
  newRoleName,
  newRolePermissions,
  rbacRoleSaveBusy,
  rbacRolesBusy,
  rbacRoles,
  assignUserId,
  assignRoleName,
  rbacAssignBusy,
  rbacAssignmentsBusy,
  assignmentUserFilter,
  assignmentRoleFilter,
  rbacAssignmentRows,
  rbacAssignmentsCount,
  rbacFilterBadges,
  rbacRevokeBusyKey,
  onNewRoleNameChange,
  onNewRolePermissionsChange,
  onSaveRbacRole,
  onLoadRbacRoles,
  onAssignUserIdChange,
  onAssignRoleNameChange,
  onAssignRbacRole,
  onLoadRbacAssignments,
  onClearRbacFilters,
  onAssignmentUserFilterChange,
  onAssignmentRoleFilterChange,
  onRevokeRbacRole,
}: AdminRbacTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("rbacRolesTitle", "Roles and permissions")}</h2>
        <p className="subText">{tx("rbacRolesHelp", "Create or update role with comma-separated permissions.")}</p>
        {rbacFeedback ? (
          <p className={`inlineFeedback inlineFeedback${rbacFeedback.tone === "error" ? "Error" : rbacFeedback.tone === "success" ? "Success" : "Info"}`}>
            {rbacFeedback.message}
          </p>
        ) : null}
        <div className="formGrid compactFormGrid">
          <input value={newRoleName} onChange={(e) => onNewRoleNameChange(e.target.value)} placeholder={tx("rbacRoleName", "Role name")} />
          <input value={newRolePermissions} onChange={(e) => onNewRolePermissionsChange(e.target.value)} placeholder={tx("rbacPermissions", "Permissions: admin.dashboard.read,admin.audit.read")} />
        </div>
        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onSaveRbacRole()} disabled={rbacRoleSaveBusy}>
            {rbacRoleSaveBusy ? tx("saving", "Saving...") : tx("rbacSaveRole", "Save role")}
          </button>
          <button type="button" className="ghost" onClick={() => void onLoadRbacRoles()} disabled={rbacRolesBusy}>
            {rbacRolesBusy ? tx("loading", "Loading...") : tx("rbacRefresh", "Refresh")}
          </button>
        </div>

        {rbacRoles.length === 0 ? (
          <p className="subText">{tx("rbacNoRoles", "No roles found.")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("rbacRole", "Role")}</th>
                  <th>{tx("rbacPerms", "Permissions")}</th>
                </tr>
              </thead>
              <tbody>
                {rbacRoles.map((row) => (
                  <tr key={row.name}>
                    <td><b>{row.name}</b></td>
                    <td>
                      {row.permissions.length === 0 ? "-" : (
                        <div className="badgeRow">
                          {row.permissions.map((permission) => (
                            <span key={`${row.name}:${permission}`} className="badge badgeInfo">{permission}</span>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </article>

      <article className="panelCard">
        <h2>{tx("rbacAssignTitle", "Assign role")}</h2>
        <p className="subText">{tx("rbacAssignHelp", "Assign a role to a specific user ID.")}</p>
        <div className="formGrid compactFormGrid">
          <input value={assignUserId} onChange={(e) => onAssignUserIdChange(e.target.value)} placeholder={tx("rbacUserId", "User ID")} />
          <select value={assignRoleName} onChange={(e) => onAssignRoleNameChange(e.target.value)}>
            {rbacRoles.length === 0 ? (
              <option value="">{tx("rbacNoRoles", "No roles found.")}</option>
            ) : (
              rbacRoles.map((row) => (
                <option key={row.name} value={row.name}>{row.name}</option>
              ))
            )}
          </select>
        </div>
        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onAssignRbacRole()} disabled={rbacAssignBusy || rbacRolesBusy}>
            {rbacAssignBusy ? tx("saving", "Saving...") : tx("rbacAssign", "Assign role")}
          </button>
          <button type="button" className="ghost" onClick={() => void onLoadRbacAssignments()} disabled={rbacAssignmentsBusy}>
            {rbacAssignmentsBusy ? tx("loading", "Loading...") : tx("rbacRefreshAssignments", "Refresh assignments")}
          </button>
          <button type="button" className="ghost" onClick={onClearRbacFilters} disabled={rbacAssignmentsBusy}>
            {tx("clearFilters", "Clear filters")}
          </button>
        </div>

        <div className="formGrid compactFormGrid" style={{ marginTop: 10 }}>
          <input value={assignmentUserFilter} onChange={(e) => onAssignmentUserFilterChange(e.target.value)} placeholder={tx("rbacFilterUser", "Filter by user ID")} />
          <input value={assignmentRoleFilter} onChange={(e) => onAssignmentRoleFilterChange(e.target.value)} placeholder={tx("rbacFilterRole", "Filter by role")} />
        </div>
        <div className="rowMeta">
          <span className="subText">{tx("rbacResults", "Assignments shown")}: {rbacAssignmentRows.length}</span>
          {rbacFilterBadges.length > 0 ? (
            <div className="badgeRow">
              {rbacFilterBadges.map((badge) => (
                <span key={badge} className="badge badgeInfo">{badge}</span>
              ))}
            </div>
          ) : null}
        </div>

        {rbacAssignmentsCount === 0 ? (
          <p className="subText">{tx("rbacNoAssignments", "No assignments found.")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("rbacUserId", "User ID")}</th>
                  <th>{tx("rbacRole", "Role")}</th>
                  <th>{l.actions}</th>
                </tr>
              </thead>
              <tbody>
                {rbacAssignmentRows.map((row) => (
                  <tr key={`${row.user_id}:${row.role}`}>
                    <td>{row.user_id}</td>
                    <td>{row.role}</td>
                    <td className="actionCell">
                      <button type="button" className="ghost danger" onClick={() => void onRevokeRbacRole(row.user_id, row.role)} disabled={rbacRevokeBusyKey === `${row.user_id}:${row.role}`}>
                        {rbacRevokeBusyKey === `${row.user_id}:${row.role}` ? tx("deleting", "Deleting...") : tx("rbacRevoke", "Revoke")}
                      </button>
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