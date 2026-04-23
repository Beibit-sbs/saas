"use client";

import { useState } from "react";
import { BarChart3 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useCreateEvalRun,
  useLeaderboard,
  useListEvalRuns,
} from "@/modules/model-evaluation/hooks";

export default function ModelEvaluationPage() {
  const [modelName, setModelName] = useState("");
  const [evalSetName, setEvalSetName] = useState("");

  const createRun = useCreateEvalRun();
  const { data: runs } = useListEvalRuns();
  const { data: leaderboard } = useLeaderboard();

  return (
    <RequirePermission permission={PERMISSIONS.MODEL_EVALUATION_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Model Evaluation"
          description="Track model quality metrics, evaluation runs, and leaderboard rankings"
          icon={BarChart3}
        />

        <RequirePermission permission={PERMISSIONS.MODEL_EVALUATION_WRITE}>
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <h2 className="text-lg font-semibold">Create Evaluation Run</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="me_model">Model Name</Label>
                <Input
                  id="me_model"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  placeholder="gpt-4o"
                />
              </div>
              <div>
                <Label htmlFor="me_dataset">Eval Set Name</Label>
                <Input
                  id="me_dataset"
                  value={evalSetName}
                  onChange={(e) => setEvalSetName(e.target.value)}
                  placeholder="academic-qa-v1"
                />
              </div>
            </div>
            <Button
              disabled={createRun.isPending || !modelName || !evalSetName}
              onClick={() =>
                createRun.mutate({
                  model_name: modelName,
                  eval_set_name: evalSetName,
                })
              }
            >
              {createRun.isPending ? "Creating..." : "Create Run"}
            </Button>
          </div>
        </RequirePermission>

        {leaderboard && leaderboard.length > 0 && (
          <div className="rounded-lg border bg-card">
            <div className="p-4 border-b">
              <h2 className="text-lg font-semibold">Leaderboard</h2>
            </div>
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40">
                <tr>
                  <th className="text-left p-3">Rank</th>
                  <th className="text-left p-3">Model</th>
                  <th className="text-left p-3">Eval Set</th>
                  <th className="text-left p-3">Score</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((e) => (
                  <tr key={e.run_id} className="border-b last:border-0">
                    <td className="p-3 font-bold">#{e.rank}</td>
                    <td className="p-3 font-medium">{e.model_name}</td>
                    <td className="p-3">{e.eval_set_name}</td>
                    <td className="p-3">{e.primary_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="rounded-lg border bg-card">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Evaluation Runs</h2>
          </div>
          {!runs || runs.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">No evaluation runs found.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40">
                <tr>
                  <th className="text-left p-3">Eval Set</th>
                  <th className="text-left p-3">Model</th>
                  <th className="text-left p-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id} className="border-b last:border-0">
                    <td className="p-3 font-medium">{r.eval_set_name}</td>
                    <td className="p-3">{r.model_name}</td>
                    <td className="p-3 capitalize">{r.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </RequirePermission>
  );
}
