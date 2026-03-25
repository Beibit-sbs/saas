import type { AdminCopy, InlineFeedback, LocalUser, SupportedLanguage, TxFn } from "../types";

type AdminLocalUsersTabProps = {
  l: AdminCopy;
  tx: TxFn;
  supportedLanguages: SupportedLanguage[];
  localFeedback: InlineFeedback | null;
  localLogin: string;
  localPassword: string;
  localDisplayName: string;
  localRoles: string;
  localDefaultLanguage: string;
  localCreateBusy: boolean;
  localListBusy: boolean;
  localSearch: string;
  localRoleFilter: string;
  localLanguageFilter: string;
  localUsers: LocalUser[];
  localFilterBadges: string[];
  selectedLocalUser: LocalUser | null;
  selectedLocalUserId: string;
  editLocalDisplayName: string;
  editLocalLanguage: string;
  editLocalRoles: string;
  editLocalPassword: string;
  editLocalPasswordConfirm: string;
  localUpdateHasChanges: boolean;
  localUpdateBusy: boolean;
  localDeleteBusy: boolean;
  localPasswordBusy: boolean;
  onLocalLoginChange: (value: string) => void;
  onLocalPasswordChange: (value: string) => void;
  onLocalDisplayNameChange: (value: string) => void;
  onLocalRolesChange: (value: string) => void;
  onLocalDefaultLanguageChange: (value: string) => void;
  onCreateLocalUser: () => void | Promise<void>;
  onRefreshLocalUsers: () => void | Promise<void>;
  onLocalSearchChange: (value: string) => void;
  onLocalRoleFilterChange: (value: string) => void;
  onLocalLanguageFilterChange: (value: string) => void;
  onClearLocalFilters: () => void | Promise<void>;
  onSelectLocalUser: (userId: string) => void;
  onEditLocalDisplayNameChange: (value: string) => void;
  onEditLocalLanguageChange: (value: string) => void;
  onEditLocalRolesChange: (value: string) => void;
  onUpdateLocalUser: () => void | Promise<void>;
  onRevertLocalUserForm: () => void;
  onDeleteLocalUser: () => void | Promise<void>;
  onEditLocalPasswordChange: (value: string) => void;
  onEditLocalPasswordConfirmChange: (value: string) => void;
  onUpdateLocalUserPassword: () => void | Promise<void>;
};

export function AdminLocalUsersTab(props: AdminLocalUsersTabProps) {
  const {
    l,
    tx,
    supportedLanguages,
    localFeedback,
    localLogin,
    localPassword,
    localDisplayName,
    localRoles,
    localDefaultLanguage,
    localCreateBusy,
    localListBusy,
    localSearch,
    localRoleFilter,
    localLanguageFilter,
    localUsers,
    localFilterBadges,
    selectedLocalUser,
    selectedLocalUserId,
    editLocalDisplayName,
    editLocalLanguage,
    editLocalRoles,
    editLocalPassword,
    editLocalPasswordConfirm,
    localUpdateHasChanges,
    localUpdateBusy,
    localDeleteBusy,
    localPasswordBusy,
    onLocalLoginChange,
    onLocalPasswordChange,
    onLocalDisplayNameChange,
    onLocalRolesChange,
    onLocalDefaultLanguageChange,
    onCreateLocalUser,
    onRefreshLocalUsers,
    onLocalSearchChange,
    onLocalRoleFilterChange,
    onLocalLanguageFilterChange,
    onClearLocalFilters,
    onSelectLocalUser,
    onEditLocalDisplayNameChange,
    onEditLocalLanguageChange,
    onEditLocalRolesChange,
    onUpdateLocalUser,
    onRevertLocalUserForm,
    onDeleteLocalUser,
    onEditLocalPasswordChange,
    onEditLocalPasswordConfirmChange,
    onUpdateLocalUserPassword,
  } = props;

  return (
    <>
      <h2>{l.localUsersNoAd}</h2>
      <p className="subText">{l.localUsersHelp}</p>
      {localFeedback ? (
        <p className={`inlineFeedback inlineFeedback${localFeedback.tone === "error" ? "Error" : localFeedback.tone === "success" ? "Success" : "Info"}`}>
          {localFeedback.message}
        </p>
      ) : null}
      <div className="formGrid">
        <input value={localLogin} onChange={(e) => onLocalLoginChange(e.target.value)} placeholder={l.loginPlaceholder} />
        <input value={localPassword} onChange={(e) => onLocalPasswordChange(e.target.value)} placeholder={l.passwordPlaceholder} type="password" />
        <input value={localDisplayName} onChange={(e) => onLocalDisplayNameChange(e.target.value)} placeholder={l.displayNamePlaceholder} />
        <input value={localRoles} onChange={(e) => onLocalRolesChange(e.target.value)} placeholder={l.rolesPlaceholder} />
        <select value={localDefaultLanguage} onChange={(e) => onLocalDefaultLanguageChange(e.target.value)}>
          {supportedLanguages.map((lang) => (
            <option key={lang.code} value={lang.code}>{lang.native_name} ({lang.code})</option>
          ))}
        </select>
        <div className="rowButtons">
          <button type="button" onClick={() => void onCreateLocalUser()} className="primary" disabled={localCreateBusy}>
            {localCreateBusy ? tx("saving") : l.addLocalUser}
          </button>
          <button type="button" onClick={() => void onRefreshLocalUsers()} className="ghost" disabled={localListBusy}>{l.refreshList}</button>
        </div>
      </div>

      <div className="formGrid compactFormGrid mt-3">
        <input value={localSearch} onChange={(e) => onLocalSearchChange(e.target.value)} placeholder={tx("localSearch")} />
        <input value={localRoleFilter} onChange={(e) => onLocalRoleFilterChange(e.target.value)} placeholder={tx("localRoleFilter")} />
        <select value={localLanguageFilter} onChange={(e) => onLocalLanguageFilterChange(e.target.value)}>
          <option value="">{tx("localLanguageAll")}</option>
          {supportedLanguages.map((lang) => (
            <option key={lang.code} value={lang.code}>{lang.native_name} ({lang.code})</option>
          ))}
        </select>
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onRefreshLocalUsers()} disabled={localListBusy}>{tx("localApplyFilters")}</button>
          <button type="button" className="ghost" onClick={() => void onClearLocalFilters()} disabled={localListBusy}>{tx("localClearFilters")}</button>
        </div>
      </div>
      <div className="rowMeta">
        <span className="subText">{tx("localResultCount")}: {localUsers.length}</span>
        {localFilterBadges.length > 0 ? (
          <div className="badgeRow mt-0">
            {localFilterBadges.map((item) => (
              <span key={item} className="badge badgeInfo">{item}</span>
            ))}
          </div>
        ) : (
          <span className="subText">{tx("localFiltersNone")}</span>
        )}
      </div>

      {localUsers.length === 0 ? (
        <p className="subText">{l.noLocalUsers}</p>
      ) : (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>{l.user}</th>
                <th>{l.userId}</th>
                <th>{l.roles}</th>
                <th>{l.languages}</th>
                <th>{l.source}</th>
              </tr>
            </thead>
            <tbody>
              {localUsers.map((item) => (
                <tr key={item.user_id}>
                  <td><b>{item.display_name}</b> ({item.login})</td>
                  <td>{item.user_id}</td>
                  <td>{item.roles.join(", ")}</td>
                  <td>{item.default_language}</td>
                  <td>{item.auth_source} / {l.adSync}: {item.sync_with_ad ? l.on : l.off}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {localUsers.length > 0 ? (
        <article className="panelCard mt-4">
          <h3>{tx("localUserOps")}</h3>
          <p className="subText">
            {tx("localSelectedUser")}: {selectedLocalUser ? `${selectedLocalUser.display_name} (${selectedLocalUser.login}) [${selectedLocalUser.user_id}]` : "-"}
          </p>
          <div className="formGrid compactFormGrid">
            <select value={selectedLocalUserId} onChange={(e) => onSelectLocalUser(e.target.value)}>
              {localUsers.map((item) => (
                <option key={item.user_id} value={item.user_id}>{item.display_name} ({item.user_id})</option>
              ))}
            </select>
            <input value={editLocalDisplayName} onChange={(e) => onEditLocalDisplayNameChange(e.target.value)} placeholder={tx("localEditDisplayName")} />
            <select value={editLocalLanguage} onChange={(e) => onEditLocalLanguageChange(e.target.value)}>
              {supportedLanguages.map((lang) => (
                <option key={lang.code} value={lang.code}>{lang.native_name} ({lang.code})</option>
              ))}
            </select>
            <input value={editLocalRoles} onChange={(e) => onEditLocalRolesChange(e.target.value)} placeholder={tx("localEditRoles")} />
            <div className="rowButtons">
              <button type="button" className="primary" onClick={() => void onUpdateLocalUser()} disabled={!localUpdateHasChanges || localUpdateBusy}>
                {localUpdateBusy ? tx("saving") : tx("localUpdate")}
              </button>
              <button type="button" className="ghost" onClick={onRevertLocalUserForm} disabled={localUpdateBusy}>
                {tx("localRevert")}
              </button>
              <button type="button" className="ghost danger" onClick={() => void onDeleteLocalUser()} disabled={localDeleteBusy}>
                {localDeleteBusy ? tx("deleting") : tx("localDelete")}
              </button>
            </div>
          </div>
          <div className="formGrid compactFormGrid mt-2">
            <input type="password" value={editLocalPassword} onChange={(e) => onEditLocalPasswordChange(e.target.value)} placeholder={tx("localSetPassword")} />
            <input type="password" value={editLocalPasswordConfirm} onChange={(e) => onEditLocalPasswordConfirmChange(e.target.value)} placeholder={tx("localConfirmPassword")} />
            <div className="rowButtons">
              <button type="button" className="ghost" onClick={() => void onUpdateLocalUserPassword()} disabled={localPasswordBusy}>
                {localPasswordBusy ? tx("saving") : tx("localPasswordAction")}
              </button>
            </div>
          </div>
          <p className="subText">{tx("localPasswordHint")}</p>
        </article>
      ) : null}
    </>
  );
}