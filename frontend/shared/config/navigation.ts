import {
  LayoutDashboard,
  Building2,
  Flag,
  Briefcase,
  Bell,
  AlertTriangle,
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
  UserCog,
  ShieldCheck,
  ClipboardCheck,
  MessageSquare,
  LifeBuoy,
  Wallet,
  Home,
  Settings2,
  Wrench,
  Package,
  Globe2,
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
        label: "Control Plane",
        href: "/console/platform",
        icon: LayoutDashboard,
        permission: PERMISSIONS.DEVELOPER_PLATFORM_READ,
      },
      {
        label: "Tenants",
        href: "/console/platform/tenants",
        icon: Building2,
        permission: PERMISSIONS.TENANTS_READ,
      },
      {
        label: "Billing / Plans",
        href: "/console/platform/billing-plans",
        icon: Briefcase,
        permission: PERMISSIONS.BILLING_READ,
      },
      {
        label: "Usage / Quotas",
        href: "/console/platform/usage-quotas",
        icon: BarChart3,
        permission: PERMISSIONS.BILLING_READ,
      },
      {
        label: "Feature Flags",
        href: "/console/platform/feature-flags",
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
        label: "Interventions",
        href: "/console/interventions",
        icon: AlertTriangle,
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
        label: "Integrations / Webhooks",
        href: "/console/platform/integrations",
        icon: Network,
        permission: PERMISSIONS.DEVELOPER_PLATFORM_READ,
      },
      {
        label: "Automation",
        href: "/console/platform/automation",
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
        label: "Service Accounts",
        href: "/console/platform/service-accounts",
        icon: UserCog,
        permission: PERMISSIONS.DEVELOPER_PLATFORM_READ,
      },
      {
        label: "AI Copilot",
        href: "/console/ai/copilot",
        icon: Bot,
        permission: PERMISSIONS.AI_COPILOT_READ,
      },
      {
        label: "Brain Core",
        href: "/console/ai/brain",
        icon: Bot,
        permission: PERMISSIONS.DASHBOARD_READ,
        children: [
          {
            label: "Policy Settings",
            href: "/console/ai/brain/policy",
            icon: Settings2,
            permission: PERMISSIONS.DASHBOARD_READ,
          },
          {
            label: "Intelligence",
            href: "/console/ai/brain/intelligence",
            icon: Bot,
            permission: PERMISSIONS.DASHBOARD_READ,
          },
        ],
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
        label: "Degree Progress",
        href: "/console/degree-progress",
        icon: ClipboardList,
        permission: PERMISSIONS.DEGREE_PROGRESS_READ,
      },
      {
        label: "Scheduling",
        href: "/console/scheduling",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
      {
        label: "Events Management",
        href: "/console/events-management",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
      {
        label: "Exam Governance",
        href: "/console/exam-governance",
        icon: ClipboardCheck,
        permission: PERMISSIONS.DASHBOARD_READ,
      },
      {
        label: "Exam Proctoring",
        href: "/console/exam-proctoring",
        icon: ShieldCheck,
        permission: PERMISSIONS.DASHBOARD_READ,
      },
      {
        label: "Thesis",
        href: "/console/thesis",
        icon: BookOpen,
        permission: PERMISSIONS.TRANSCRIPTS_READ,
      },
      {
        label: "Research Ethics",
        href: "/console/research-ethics",
        icon: ShieldCheck,
        permission: PERMISSIONS.RESEARCH_READ,
      },
      {
        label: "Advising",
        href: "/console/advising",
        icon: MessageSquare,
        permission: PERMISSIONS.ADVISING_READ,
      },
      {
        label: "Student Services",
        href: "/console/student-services",
        icon: LifeBuoy,
        permission: PERMISSIONS.STUDENT_SERVICES_READ,
      },
      {
        label: "Student Life",
        href: "/console/student-life",
        icon: HeartPulse,
        permission: PERMISSIONS.STUDENT_LIFE_READ,
      },
      {
        label: "Career Services",
        href: "/console/career-services",
        icon: Briefcase,
        permission: PERMISSIONS.CAREER_SERVICES_READ,
      },
      {
        label: "Financial Aid",
        href: "/console/financial-aid",
        icon: Wallet,
        permission: PERMISSIONS.FINANCIAL_AID_READ,
      },
      {
        label: "Faculty KPIs",
        href: "/console/faculty-performance-kpis",
        icon: BarChart3,
        permission: PERMISSIONS.FACULTY_READ,
      },
      {
        label: "HR & Payroll",
        href: "/console/hr-payroll",
        icon: Briefcase,
        permission: PERMISSIONS.HR_READ,
      },
      {
        label: "Delinquency Collections",
        href: "/console/delinquency-collections",
        icon: Wallet,
        permission: PERMISSIONS.FINANCE_READ,
      },
      {
        label: "Expense Controls",
        href: "/console/expense-controls",
        icon: Wallet,
        permission: PERMISSIONS.FINANCE_READ,
      },
      {
        label: "Facilities & Work Orders",
        href: "/console/facilities-work-orders",
        icon: Wrench,
        permission: PERMISSIONS.FACILITIES_READ,
      },
      {
        label: "Asset Inventory",
        href: "/console/asset-inventory",
        icon: Package,
        permission: PERMISSIONS.ASSET_INVENTORY_READ,
      },
      {
        label: "Faculty Copilot",
        href: "/console/faculty-copilot",
        icon: Bot,
        permission: PERMISSIONS.FACULTY_COPILOT_READ,
      },
      {
        label: "Knowledge Retrieval",
        href: "/console/knowledge-retrieval",
        icon: BookOpen,
        permission: PERMISSIONS.KNOWLEDGE_RETRIEVAL_READ,
      },
      {
        label: "Prompt Management",
        href: "/console/prompt-management",
        icon: Code2,
        permission: PERMISSIONS.PROMPT_MANAGEMENT_READ,
      },
      {
        label: "Model Evaluation",
        href: "/console/model-evaluation",
        icon: BarChart3,
        permission: PERMISSIONS.MODEL_EVALUATION_READ,
      },
      {
        label: "Housing",
        href: "/console/housing",
        icon: Home,
        permission: PERMISSIONS.HOUSING_READ,
      },
      {
        label: "Alumni",
        href: "/console/alumni",
        icon: GraduationCap,
        permission: PERMISSIONS.ALUMNI_READ,
      },
      {
        label: "Academic Integrity",
        href: "/console/academic-integrity",
        icon: ShieldCheck,
        permission: PERMISSIONS.ACADEMIC_RECORDS_READ,
      },
      {
        label: "Accreditation Compliance",
        href: "/console/accreditation-compliance",
        icon: FileText,
        permission: PERMISSIONS.ACADEMIC_RECORDS_READ,
      },
      {
        label: "Admissions",
        href: "/console/admissions",
        icon: ClipboardCheck,
        permission: PERMISSIONS.ADMISSIONS_READ,
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Role-specific navigation (university pilot roles)
// ---------------------------------------------------------------------------

export const STUDENT_NAVIGATION: NavGroup[] = [
  {
    label: "My Space",
    items: [
      { label: "Dashboard", href: "/console", icon: LayoutDashboard },
      {
        label: "Schedule",
        href: "/console/scheduling",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
      {
        label: "Grades",
        href: "/console/grades",
        icon: BarChart3,
        permission: PERMISSIONS.GRADES_READ,
      },
      {
        label: "Transcript",
        href: "/console/transcripts",
        icon: FileText,
        permission: PERMISSIONS.TRANSCRIPTS_READ,
      },
    ],
  },
];

export const TEACHER_NAVIGATION: NavGroup[] = [
  {
    label: "My Work",
    items: [
      { label: "Dashboard", href: "/console", icon: LayoutDashboard },
      {
        label: "Students",
        href: "/console/students",
        icon: GraduationCap,
        permission: PERMISSIONS.STUDENTS_READ,
      },
      {
        label: "Grades",
        href: "/console/grades",
        icon: BarChart3,
        permission: PERMISSIONS.GRADES_READ,
      },
      {
        label: "Schedule",
        href: "/console/scheduling",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
      {
        label: "Requests",
        href: "/console/enrollments",
        icon: ClipboardCheck,
        permission: PERMISSIONS.ENROLLMENTS_READ,
      },
    ],
  },
];

export const DEAN_NAVIGATION: NavGroup[] = [
  {
    label: "Faculty",
    items: [
      { label: "Dashboard", href: "/console", icon: LayoutDashboard },
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
        label: "Scheduling",
        href: "/console/scheduling",
        icon: CalendarDays,
        permission: PERMISSIONS.SCHEDULING_READ,
      },
    ],
  },
];

export const SUPERADMIN_NAVIGATION: NavGroup[] = [
  {
    label: "Overview",
    items: [{ label: "Dashboard", href: "/console", icon: LayoutDashboard }],
  },
  {
    label: "Platform Management",
    items: [
      {
        label: "Control Plane",
        href: "/console/platform",
        icon: LayoutDashboard,
      },
      {
        label: "Tenants",
        href: "/console/platform/tenants",
        icon: Building2,
      },
      {
        label: "Billing / Plans",
        href: "/console/platform/billing-plans",
        icon: Briefcase,
      },
      {
        label: "Usage / Quotas",
        href: "/console/platform/usage-quotas",
        icon: BarChart3,
      },
      {
        label: "Feature Flags",
        href: "/console/platform/feature-flags",
        icon: Flag,
      },
      {
        label: "Integrations / Webhooks",
        href: "/console/platform/integrations",
        icon: Network,
      },
      {
        label: "Automation",
        href: "/console/platform/automation",
        icon: Bot,
      },
      {
        label: "Service Accounts",
        href: "/console/platform/service-accounts",
        icon: UserCog,
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        label: "Jobs",
        href: "/console/jobs",
        icon: Briefcase,
        permission: PERMISSIONS.JOBS_READ,
      },
      {
        label: "Interventions",
        href: "/console/interventions",
        icon: AlertTriangle,
        permission: PERMISSIONS.JOBS_READ,
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
        label: "Profiles",
        href: "/console/profiles",
        icon: UserCog,
        permission: PERMISSIONS.PROFILES_READ,
      },
    ],
  },
  {
    label: "Users & Roles",
    items: [
      {
        label: "Local Users",
        href: "/console/local-users",
        icon: UserCog,
        permission: PERMISSIONS.LOCAL_USERS_MANAGE,
      },
      {
        label: "RBAC",
        href: "/console/rbac",
        icon: ShieldCheck,
        permission: PERMISSIONS.ROLES_MANAGE,
      },
      {
        label: "Identity & Access",
        href: "/console/identity",
        icon: ShieldCheck,
        permission: PERMISSIONS.INTEGRATIONS_MANAGE,
      },
      {
        label: "LDAP",
        href: "/console/ldap",
        icon: Network,
        permission: PERMISSIONS.INTEGRATIONS_MANAGE,
      },
      {
        label: "Languages",
        href: "/console/languages",
        icon: Code2,
        permission: PERMISSIONS.I18N_MANAGE,
      },
      {
        label: "Currency Localization",
        href: "/console/currency-localization",
        icon: Globe2,
        permission: PERMISSIONS.I18N_MANAGE,
      },
      {
        label: "Workflows",
        href: "/console/workflows",
        icon: Bot,
        permission: PERMISSIONS.WORKFLOWS_READ,
      },
    ],
  },
  {
    label: "Rector Assignments",
    items: [
      {
        label: "Assignment Registry",
        href: "/console/rector-assignments",
        icon: ClipboardList,
        permission: PERMISSIONS.RECTOR_ASSIGNMENTS_DASHBOARD_READ,
      },
      {
        label: "My Assignments",
        href: "/console/my-assignments",
        icon: ClipboardCheck,
        permission: PERMISSIONS.RECTOR_ASSIGNMENTS_LIST,
      },
      {
        label: "Templates",
        href: "/console/rector-assignments/templates",
        icon: Package,
        permission: PERMISSIONS.RECTOR_ASSIGNMENTS_TEMPLATES_MANAGE,
      },
      {
        label: "Overdue & Escalations",
        href: "/console/rector-assignments/overdue",
        icon: AlertTriangle,
        permission: PERMISSIONS.RECTOR_ASSIGNMENTS_DASHBOARD_READ,
      },
    ],
  },
];

/**
 * Returns the navigation config appropriate for the user's primary role.
 * Priority: superadmin/admin > student > teacher > dean > platform nav.
 */
export function getNavigationForRoles(roles: string[]): NavGroup[] {
  if (roles.includes("superadmin") || roles.includes("admin"))
    return SUPERADMIN_NAVIGATION;
  if (roles.includes("student")) return STUDENT_NAVIGATION;
  if (roles.includes("teacher")) return TEACHER_NAVIGATION;
  if (roles.includes("dean")) return DEAN_NAVIGATION;
  return NAVIGATION;
}
