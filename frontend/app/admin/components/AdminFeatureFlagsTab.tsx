import type { FeatureFlag, InlineFeedback, TxFn } from "../types";
import { formatFeatureFlagLastChange } from "../utils";

type AdminFeatureFlagsTabProps = {
  tx: TxFn;
  featureFlagsLoading: boolean;
  featureFlagsMutating: boolean;
  featureFlagSearch: string;
  featureFlagEnabledOnly: boolean;
  featureFlagsFeedback: InlineFeedback | null;
  featureFlagSummary: string;
  hasActiveFeatureFlagFilters: boolean;
  featureFlagFilterBadges: string[];
  filteredFeatureFlags: FeatureFlag[];
  featureFlagUpdateBusy: Record<string, boolean>;
  onLoadFeatureFlags: () => void | Promise<void>;
  onFeatureFlagSearchChange: (value: string) => void;
  onFeatureFlagEnabledOnlyChange: (value: boolean) => void;
  onSetFeatureFlagEnabled: (flag: FeatureFlag, enabled: boolean) => void | Promise<void>;
};

export function AdminFeatureFlagsTab({
  tx,
  featureFlagsLoading,
  featureFlagsMutating,
  featureFlagSearch,
  featureFlagEnabledOnly,
  featureFlagsFeedback,
  featureFlagSummary,
  hasActiveFeatureFlagFilters,
  featureFlagFilterBadges,
  filteredFeatureFlags,
  featureFlagUpdateBusy,
  onLoadFeatureFlags,
  onFeatureFlagSearchChange,
  onFeatureFlagEnabledOnlyChange,
  onSetFeatureFlagEnabled,
}: AdminFeatureFlagsTabProps) {
  return (
    <div className="grid2">
      <article className="panelCard">
        <h2>{tx("featureFlags", "Feature Flags")}</h2>
        <p className="subText">{tx("featureFlagsHelp", "Use flags to safely roll out operational features.")}</p>
        <div className="rowButtons">
          <button type="button" className="ghost" onClick={() => void onLoadFeatureFlags()} disabled={featureFlagsLoading || featureFlagsMutating}>
            {featureFlagsLoading ? tx("featureFlagsLoading", "Loading...") : tx("overviewRefresh", "Refresh snapshot")}
          </button>
        </div>
        <div className="formGrid compactFormGrid">
          <input value={featureFlagSearch} onChange={(e) => onFeatureFlagSearchChange(e.target.value)} placeholder={tx("featureFlagSearch", "Search by key or description")} />
          <label className="toggleRow">
            <input type="checkbox" checked={featureFlagEnabledOnly} onChange={(e) => onFeatureFlagEnabledOnlyChange(e.target.checked)} />
            {tx("featureFlagsEnabledOnly", "Show enabled only")}
          </label>
        </div>
        {featureFlagsFeedback ? (
          <p className={`inlineFeedback inlineFeedback${featureFlagsFeedback.tone === "error" ? "Error" : featureFlagsFeedback.tone === "success" ? "Success" : "Info"}`}>
            {featureFlagsFeedback.message}
          </p>
        ) : null}
        <div className="rowMeta">
          <span className="subText">{featureFlagSummary}</span>
          {hasActiveFeatureFlagFilters ? (
            <div className="badgeRow featureFlagFilterBadges">
              {featureFlagFilterBadges.map((item) => (
                <span key={item} className="badge badgeInfo">{item}</span>
              ))}
            </div>
          ) : (
            <span className="subText">{tx("featureFlagsNoFiltersActive", "No active filters")}</span>
          )}
        </div>
        {filteredFeatureFlags.length === 0 ? (
          <p className="subText">{tx("featureFlagsEmpty", "No feature flags found.")}</p>
        ) : (
          <div className="featureFlagList">
            {filteredFeatureFlags.map((flag) => {
              const rowBusy = Boolean(featureFlagUpdateBusy[flag.key]);
              const lastChanged = formatFeatureFlagLastChange(flag);
              return (
                <div className="featureFlagRow" key={flag.key}>
                  <div className="featureFlagInfo">
                    <p className="featureFlagKey">{flag.key}</p>
                    <p className="subText">{flag.description || "-"}</p>
                    <div className="badgeRow featureFlagBadges">
                      <span className={`badge ${flag.enabled ? "badgeOk" : "badgeWarn"}`}>{flag.enabled ? tx("enabled", "Enabled") : tx("disabled", "Disabled")}</span>
                      <span className="badge badgeInfo">{flag.scope || "global"}</span>
                    </div>
                    {lastChanged ? <p className="subText featureFlagLastChanged">{tx("featureFlagLastChanged", "Last changed")}: {lastChanged}</p> : null}
                  </div>
                  <div className="featureFlagActions">
                    <button type="button" className={`featureFlagSwitch ${flag.enabled ? "featureFlagSwitchOn" : ""}`} aria-label={`${flag.enabled ? tx("disable", "Disable") : tx("enable", "Enable")} ${flag.key}`} onClick={() => void onSetFeatureFlagEnabled(flag, !flag.enabled)} disabled={featureFlagsLoading || featureFlagsMutating}>
                      <span className="featureFlagSwitchKnob" />
                    </button>
                    <button type="button" className="ghost" onClick={() => void onSetFeatureFlagEnabled(flag, !flag.enabled)} disabled={featureFlagsLoading || featureFlagsMutating}>
                      {rowBusy ? tx("featureFlagUpdating", "Updating...") : flag.enabled ? tx("disable", "Disable") : tx("enable", "Enable")}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </article>
    </div>
  );
}