import type { AdminCopy, CatalogLanguage, SupportedLanguage } from "../types";

type AdminLanguagesTabProps = {
  l: AdminCopy;
  catalogQuery: string;
  availableCatalogLanguages: CatalogLanguage[];
  selectedCatalogCode: string;
  selectedCatalogLanguage: CatalogLanguage | null;
  supportedLanguages: SupportedLanguage[];
  defaultLanguage: string;
  onCatalogQueryChange: (value: string) => void;
  onSelectCatalogCode: (code: string) => void;
  onAddLanguage: () => void | Promise<void>;
  onSetDefaultLanguage: (code: string) => void | Promise<void>;
  onToggleLanguageEnabled: (code: string, enabled: boolean) => void | Promise<void>;
  onDeleteLanguage: (code: string) => void | Promise<void>;
};

export function AdminLanguagesTab({
  l,
  catalogQuery,
  availableCatalogLanguages,
  selectedCatalogCode,
  selectedCatalogLanguage,
  supportedLanguages,
  defaultLanguage,
  onCatalogQueryChange,
  onSelectCatalogCode,
  onAddLanguage,
  onSetDefaultLanguage,
  onToggleLanguageEnabled,
  onDeleteLanguage,
}: AdminLanguagesTabProps) {
  const enabledLanguages = supportedLanguages.filter((lang) => lang.enabled);

  return (
    <>
      <h2>{l.languageManagement}</h2>
      <p className="subText">{l.langHelp}</p>
      <div className="languagePickerGrid">
        <article className="catalogCard">
          <h3>{l.catalogTitle}</h3>
          <p className="subText">{l.catalogHelp}</p>
          <input
            value={catalogQuery}
            onChange={(e) => onCatalogQueryChange(e.target.value)}
            placeholder={l.searchLanguagePlaceholder}
          />
          <div className="catalogList" role="listbox" aria-label={l.catalogTitle}>
            {availableCatalogLanguages.length === 0 ? (
              <p className="subText">{l.noCatalogResults}</p>
            ) : (
              availableCatalogLanguages.map((item) => (
                <button
                  key={item.code}
                  type="button"
                  className={selectedCatalogCode === item.code ? "catalogItem catalogItemActive" : "catalogItem"}
                  onClick={() => onSelectCatalogCode(item.code)}
                >
                  <span>
                    <b>{item.native_name}</b> ({item.code})
                  </span>
                  <small>{item.name}</small>
                </button>
              ))
            )}
          </div>
        </article>

        <article className="catalogCard">
          <h3>{l.selectedLanguage}</h3>
          {selectedCatalogLanguage ? (
            <div className="selectedLanguageCard">
              <p>
                <b>{selectedCatalogLanguage.native_name}</b>
              </p>
              <p>{selectedCatalogLanguage.name}</p>
              <div className="badgeRow">
                <span className="badge">
                  {l.code}: {selectedCatalogLanguage.code}
                </span>
              </div>
              <button type="button" onClick={() => void onAddLanguage()} className="primary">
                {l.addLanguage}
              </button>
            </div>
          ) : (
            <p className="subText">{l.noLanguageSelected}</p>
          )}
        </article>
      </div>

      <article className="catalogCard" style={{ marginTop: 12 }}>
        <h3>{l.defaultLanguageTitle}</h3>
        <p className="subText">{l.defaultLanguageHelp}</p>
        <div className="inlineRow" style={{ gap: 10, alignItems: "center" }}>
          <select value={defaultLanguage} onChange={(e) => void onSetDefaultLanguage(e.target.value)}>
            {enabledLanguages.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.native_name} ({lang.code})
              </option>
            ))}
          </select>
          <button type="button" className="ghost" onClick={() => void onSetDefaultLanguage(defaultLanguage)}>
            {l.setDefaultLanguage}
          </button>
        </div>
      </article>

      <div className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>{l.code}</th>
              <th>{l.name}</th>
              <th>{l.type}</th>
              <th>{l.status}</th>
              <th>{l.actions}</th>
            </tr>
          </thead>
          <tbody>
            {supportedLanguages.map((lang) => (
              <tr key={lang.code}>
                <td>
                  <b>{lang.code}</b>
                </td>
                <td>
                  {lang.native_name} ({lang.name})
                </td>
                <td>{lang.system ? l.system : l.custom}</td>
                <td>{lang.enabled ? l.enabled : l.disabled}</td>
                <td className="actionCell">
                  <button type="button" onClick={() => void onToggleLanguageEnabled(lang.code, !lang.enabled)} className="ghost">
                    {lang.enabled ? l.disable : l.enable}
                  </button>
                  <button type="button" onClick={() => void onDeleteLanguage(lang.code)} className="ghost danger">
                    {l.delete}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
