export interface Notification {
  id: string;
  type: string;
  severity: "info" | "warning" | "error" | "success";
  title: string;
  body: string;
  tenant_id: string | null;
  read: boolean;
  created_at: string;
}
