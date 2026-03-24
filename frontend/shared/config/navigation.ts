import {
  LayoutDashboard,
  Building2,
  Flag,
  Briefcase,
  Bell,
  HeartPulse,
  Bot,
  GraduationCap,
  BookOpen,
  ClipboardList,
  BarChart3,
  FileText,
  CalendarDays,
  Network,
  Code2,
  type LucideIcon,
} from "lucide-react";
import { PERMISSIONS, type Permission } from "./permissions";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: Permission;
  children?: NavItem[];
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

export const NAVIGATION: NavGroup[] = [
  {
    label: "Overview",
    items: [
      {
        label: "Dashboard",
        href: "/console",
        icon: LayoutDashboard,
      },
    ],
  },
  {
    label: "Platform",
    items: [
      {
        label: "Tenants",
        href: "/console/tenants",
        icon: Building2,
        permission: PERMISSIONS.TENANTS_READ,
      },
      {
        label: "Feature Flags",
        href: "/console/feature-flags",
        icon: Flag,
        permission: PERMISSIONS.FEATURE_FLAGS_READ,
      },
      {
        label: "Jobs",
        href: "/console/jobs",
        icon: Briefcase,
        permission: PERMISSIONS.JOBS_READ,
      },
      {
        label: "Notifications",
        href: "/console/notifications",
        icon: Bell,
        permission: PERMISSIONS.NOTIFICATIONS_READ,
      },
      {
        label: "Health & Metrics",
        href: "/console/health",
        icon: HeartPulse,
        permission: PERMISSIONS.HEALTH_READ,
      },
      {
        label: "Platform Ops",
        href: "/console/ops",
        icon: HeartPulse,
        permission: PERMISSIONS.OPS_READ,
      },
      {
        label: "Automation",
        href: "/console/automation",
        icon: Bot,
        permission: PERMISSIONS.AUTOMATION_READ,
        children: [
          {
            label: "Rules",
            href: "/console/automation",
            icon: Bot,
          },
          {
            label: "Executions",
            href: "/console/automation/executions",
            icon: ClipboardList,
          },
        ],
      },
      {
        label: "AI Copilot",
        href: "/console/ai/copilot",
        icon: Bot,
        permission: PERMISSIONS.AI_COPILOT_READ,
      },
      {
        label: "Federation",
        href: "/console/federation",
        icon: Network,
        permission: PERMISSIONS.FEDERATION_READ,
      },
      {
        label: "Developer Apps",
        href: "/console/developer/apps",
        icon: Code2,
        permission: PERMISSIONS.DEVELOPER_PLATFORM_READ,
      },
    ],
  },
  {
    label: "Academic",
    items: [
      {
        label: "Students",
        href: "/console/students",
        icon: GraduationCap,
        permission: PERMISSIONS.STUDENTS_READ,
      },
      {
        label: "Enrollments",
        href: "/console/enrollments",
        icon: BookOpen,
        permission: PERMISSIONS.ENROLLMENTS_READ,
      },
      {
        label: "Grades",
        href: "/console/grades",
        icon: BarChart3,
        permission: PERMISSIONS.GRADES_READ,
      },
      {
        label: "Transcripts",
        href: "/console/transcripts",
        icon: FileText,
        permission: PERMISSIONS.TRANSCRIPTS_READ,
      },
      {
        label: "Scheduling",
        href: "/console/scheduling",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
    ],
  },
];
