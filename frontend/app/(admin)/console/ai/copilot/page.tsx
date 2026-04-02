"use client";

import { useMemo, useState } from "react";
import { Bot, Send, Lightbulb } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useAdminAuth } from "@/shared/auth/context";
import { useAskCopilot } from "@/modules/platform/ai/use-copilot";
import { useLanguage } from "@/app/components/LanguageProvider";

export default function AICopilotPage() {
  const { t } = useLanguage();
  const { user } = useAdminAuth();
  const tenantId = user?.tenantId ?? 0;
  const [question, setQuestion] = useState("");
  const ask = useAskCopilot();

  const canSubmit = useMemo(() => question.trim().length > 0 && !ask.isPending, [question, ask.isPending]);

  return (
    <RequirePermission
      permission={PERMISSIONS.AI_COPILOT_READ}
      message={t("aiCopilot.permissionDenied")}
    >
      <div className="space-y-6" data-testid="ai-copilot-page">
        <PageHeader
          title={t("aiCopilot.title")}
          description={t("aiCopilot.description")}
          icon={Bot}
        />

        <div className="rounded-lg border bg-card p-4 space-y-3">
          <label htmlFor="copilot-question" className="text-sm font-medium">
            {t("aiCopilot.askLabel")}
          </label>
          <textarea
            id="copilot-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={t("aiCopilot.placeholder")}
            className="w-full min-h-24 rounded-md border bg-background p-3 text-sm"
            data-testid="copilot-question-input"
          />
          <div className="flex justify-end">
            <Button
              onClick={() => {
                ask.mutate({ tenant_id: tenantId, question: question.trim(), context: {} });
              }}
              disabled={!canSubmit}
              data-testid="copilot-submit-btn"
            >
              <Send className="mr-2 h-4 w-4" />
              {t("aiCopilot.ask")}
            </Button>
          </div>
        </div>

        {ask.isError && (
          <ErrorState
            title={t("aiCopilot.requestFailedTitle")}
            message={t("aiCopilot.requestFailedMessage")}
            onRetry={() => {
              if (question.trim()) {
                ask.mutate({ tenant_id: tenantId, question: question.trim(), context: {} });
              }
            }}
          />
        )}

        {ask.data && (
          <div className="rounded-lg border bg-card p-4 space-y-4" data-testid="copilot-answer-panel">
            <div>
              <p className="text-xs text-muted-foreground">{t("aiCopilot.question")}</p>
              <p className="text-sm">{ask.data.question}</p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">{t("aiCopilot.summary")}</p>
              <p className="text-sm font-medium">{ask.data.summary}</p>
            </div>

            <div className="space-y-2" data-testid="copilot-insights">
              <p className="text-xs text-muted-foreground">{t("aiCopilot.insights")}</p>
              {ask.data.insights.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("aiCopilot.noInsights")}</p>
              ) : (
                ask.data.insights.map((item) => (
                  <div key={`${item.title}-${item.value}`} className="rounded border p-3">
                    <p className="text-sm font-medium">{item.title}: {item.value}</p>
                    <p className="text-xs text-muted-foreground mt-1">{item.explanation}</p>
                  </div>
                ))
              )}
            </div>

            <div className="space-y-2" data-testid="copilot-sources">
              <p className="text-xs text-muted-foreground">{t("aiCopilot.sources")}</p>
              <div className="flex flex-wrap gap-2">
                {ask.data.sources.map((source) => (
                  <Badge key={`${source.source_type}:${source.reference}`} variant="outline">
                    {source.source_type}: {source.reference}
                  </Badge>
                ))}
              </div>
            </div>

            {ask.data.warnings.length > 0 && (
              <div className="space-y-2" data-testid="copilot-warnings">
                <p className="text-xs text-muted-foreground">{t("aiCopilot.warnings")}</p>
                <div className="flex flex-wrap gap-2">
                  {ask.data.warnings.map((warning) => (
                    <Badge key={warning} variant="secondary">
                      {warning}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {ask.data.recommendations && ask.data.recommendations.length > 0 && (
              <div className="space-y-3" data-testid="copilot-recommendations">
                <div className="flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground">{t("aiCopilot.recommendations")}</p>
                </div>
                {ask.data.recommendations.map((rec) => (
                  <div
                    key={rec.recommendation_type}
                    className="rounded border p-3 space-y-2"
                    data-testid={`copilot-recommendation-${rec.recommendation_type}`}
                  >
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          rec.priority === "high"
                            ? "destructive"
                            : rec.priority === "medium"
                              ? "default"
                              : "outline"
                        }
                        data-testid="copilot-rec-priority-badge"
                      >
                        {rec.priority}
                      </Badge>
                      <p className="text-sm font-medium">{rec.title}</p>
                    </div>
                    <p className="text-xs text-muted-foreground">{rec.reason}</p>
                    {rec.suggested_actions.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {rec.suggested_actions.map((action) => (
                          <a
                            key={action.label}
                            href={action.target ?? "#"}
                            className="text-xs underline text-primary hover:opacity-80"
                            data-testid="copilot-rec-action-link"
                          >
                            {action.label}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
