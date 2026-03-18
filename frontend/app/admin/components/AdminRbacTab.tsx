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
        <h2>{tx("rbacRolesTitle")}</h2>
        <p className="subText">{tx("rbacRolesHelp")}</p>
        {rbacFeedback ? (
          <p className={`inlineFeedback inlineFeedback${rbacFeedback.tone === "error" ? "Error" : rbacFeedback.tone === "success" ? "Success" : "Info"}`}>
            {rbacFeedback.message}
          </p>
        ) : null}
        <div className="formGrid compactFormGrid">
          <input value={newRoleName} onChange={(e) => onNewRoleNameChange(e.target.value)} placeholder={tx("rbacRoleName")} />
          <input value={newRolePermissions} onChange={(e) => onNewRolePermissionsChange(e.target.value)} placeholder={tx("rbacPermissions")} />
        </div>
        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onSaveRbacRole()} disabled={rbacRoleSaveBusy}>
            {rbacRoleSaveBusy ? tx("saving") : tx("rbacSaveRole")}
          </button>
          <button type="button" className="ghost" onClick={() => void onLoadRbacRoles()} disabled={rbacRolesBusy}>
            {rbacRolesBusy ? tx("loading") : tx("rbacRefresh")}
          </button>
        </div>

        {rbacRoles.length === 0 ? (
          <p className="subText">{tx("rbacNoRoles")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("rbacRole")}</th>
                  <th>{tx("rbacPerms")}</th>
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
        <h2>{tx("rbacAssignTitle")}</h2>
        <p className="subText">{tx("rbacAssignHelp")}</p>
        <div className="formGrid compactFormGrid">
          <input value={assignUserId} onChange={(e) => onAssignUserIdChange(e.target.value)} placeholder={tx("rbacUserId")} />
          <select value={assignRoleName} onChange={(e) => onAssignRoleNameChange(e.target.value)}>
            {rbacRoles.length === 0 ? (
              <option value="">{tx("rbacNoRoles")}</option>
            ) : (
              rbacRoles.map((row) => (
                <option key={row.name} value={row.name}>{row.name}</option>
              ))
            )}
          </select>
        </div>
        <div className="rowButtons">
          <button type="button" className="primary" onClick={() => void onAssignRbacRole()} disabled={rbacAssignBusy || rbacRolesBusy}>
            {rbacAssignBusy ? tx("saving") : tx("rbacAssign")}
          </button>
          <button type="button" className="ghost" onClick={() => void onLoadRbacAssignments()} disabled={rbacAssignmentsBusy}>
            {rbacAssignmentsBusy ? tx("loading") : tx("rbacRefreshAssignments")}
          </button>
          <button type="button" className="ghost" onClick={onClearRbacFilters} disabled={rbacAssignmentsBusy}>
            {tx("clearFilters")}
          </button>
        </div>

        <div className="formGrid compactFormGrid" style={{ marginTop: 10 }}>
          <input value={assignmentUserFilter} onChange={(e) => onAssignmentUserFilterChange(e.target.value)} placeholder={tx("rbacFilterUser")} />
          <input value={assignmentRoleFilter} onChange={(e) => onAssignmentRoleFilterChange(e.target.value)} placeholder={tx("rbacFilterRole")} />
        </div>
        <div className="rowMeta">
          <span className="subText">{tx("rbacResults")}: {rbacAssignmentRows.length}</span>
          {rbacFilterBadges.length > 0 ? (
            <div className="badgeRow">
              {rbacFilterBadges.map((badge) => (
                <span key={badge} className="badge badgeInfo">{badge}</span>
              ))}
            </div>
          ) : null}
        </div>

        {rbacAssignmentsCount === 0 ? (
          <p className="subText">{tx("rbacNoAssignments")}</p>
        ) : (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>{tx("rbacUserId")}</th>
                  <th>{tx("rbacRole")}</th>
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
                        {rbacRevokeBusyKey === `${row.user_id}:${row.role}` ? tx("deleting") : tx("rbacRevoke")}
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