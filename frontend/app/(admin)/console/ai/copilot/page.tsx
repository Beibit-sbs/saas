"use client";

import { useMemo, useState } from "react";
import { Bot, Send } from "lucide-react";

import { PERMISSIONS } from "@/shared/config/permissions";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { ErrorState } from "@/shared/ui/error-state";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { useAskCopilot } from "@/modules/platform/ai/use-copilot";

export default function AICopilotPage() {
  const tenantId = 1;
  const [question, setQuestion] = useState("");
  const ask = useAskCopilot();

  const canSubmit = useMemo(() => question.trim().length > 0 && !ask.isPending, [question, ask.isPending]);

  return (
    <RequirePermission
      permission={PERMISSIONS.AI_COPILOT_READ}
      message="You need AI Copilot read permission to access this panel."
    >
      <div className="space-y-6" data-testid="ai-copilot-page">
        <PageHeader
          title="AI Copilot"
          description="Read-only deterministic assistant powered by KPI, analytics, context, and automation signals."
          icon={Bot}
        />

        <div className="rounded-lg border bg-card p-4 space-y-3">
          <label htmlFor="copilot-question" className="text-sm font-medium">
            Ask a platform question
          </label>
          <textarea
            id="copilot-question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="How many students do we currently have?"
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
              Ask
            </Button>
          </div>
        </div>

        {ask.isError && (
          <ErrorState
            title="Copilot request failed"
            message="Could not retrieve a copilot answer."
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
              <p className="text-xs text-muted-foreground">Question</p>
              <p className="text-sm">{ask.data.question}</p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground">Summary</p>
              <p className="text-sm font-medium">{ask.data.summary}</p>
            </div>

            <div className="space-y-2" data-testid="copilot-insights">
              <p className="text-xs text-muted-foreground">Insights</p>
              {ask.data.insights.length === 0 ? (
                <p className="text-sm text-muted-foreground">No insights returned.</p>
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
              <p className="text-xs text-muted-foreground">Sources</p>
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
                <p className="text-xs text-muted-foreground">Warnings</p>
                <div className="flex flex-wrap gap-2">
                  {ask.data.warnings.map((warning) => (
                    <Badge key={warning} variant="secondary">
                      {warning}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </RequirePermission>
  );
}
