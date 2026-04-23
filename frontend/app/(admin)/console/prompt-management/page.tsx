"use client";

import { useState } from "react";
import { Code2 } from "lucide-react";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { PageHeader } from "@/shared/ui/page-header";
import { RequirePermission } from "@/shared/ui/permission-gate";
import { PERMISSIONS } from "@/shared/config/permissions";
import {
  useCreateTemplate,
  useListTemplates,
} from "@/modules/prompt-management/hooks";

export default function PromptManagementPage() {
  const [name, setName] = useState("");
  const [templateText, setTemplateText] = useState("");

  const create = useCreateTemplate();
  const { data: templates } = useListTemplates();

  return (
    <RequirePermission permission={PERMISSIONS.PROMPT_MANAGEMENT_READ}>
      <div className="space-y-8">
        <PageHeader
          title="Prompt Management"
          description="Manage versioned prompt templates and A/B routing"
          icon={Code2}
        />

        <RequirePermission permission={PERMISSIONS.PROMPT_MANAGEMENT_WRITE}>
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <h2 className="text-lg font-semibold">Create Template</h2>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <Label htmlFor="pm_name">Name</Label>
                <Input
                  id="pm_name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="academic-advisor-v1"
                />
              </div>
              <div>
                <Label htmlFor="pm_text">Template Text</Label>
                <Input
                  id="pm_text"
                  value={templateText}
                  onChange={(e) => setTemplateText(e.target.value)}
                  placeholder="You are an academic advisor. {{context}}"
                />
              </div>
            </div>
            <Button
              disabled={create.isPending || !name || !templateText}
              onClick={() => create.mutate({ name, template_text: templateText })}
            >
              {create.isPending ? "Creating..." : "Create Template"}
            </Button>
          </div>
        </RequirePermission>

        <div className="rounded-lg border bg-card">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Templates</h2>
          </div>
          {!templates || templates.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">No templates found.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/40">
                <tr>
                  <th className="text-left p-3">Name</th>
                  <th className="text-left p-3">Category</th>
                  <th className="text-left p-3">Version</th>
                  <th className="text-left p-3">Active</th>
                </tr>
              </thead>
              <tbody>
                {templates.map((t) => (
                  <tr key={t.template_id} className="border-b last:border-0">
                    <td className="p-3 font-medium">{t.name}</td>
                    <td className="p-3">{t.category}</td>
                    <td className="p-3">v{t.version}</td>
                    <td className="p-3">{t.is_active ? "Yes" : "No"}</td>
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
