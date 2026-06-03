import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ADMISSIONS_CRM_ROUTES } from "@/modules/admissions-crm/routeMap";
import { AdmissionsCrmPage } from "@/modules/admissions-crm/pages";
import { ADMISSIONS_CRM_RUNTIME_PERMISSIONS } from "@/modules/admissions-crm/permissions";

const fullPermissions = [
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.READ,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.QUALIFY,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.CONVERT,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.SUBMIT,
  ADMISSIONS_CRM_RUNTIME_PERMISSIONS.AUDIT_READ,
];

describe("Admissions CRM pages", () => {
  it("renders all route keys in static test mode", () => {
    for (const route of ADMISSIONS_CRM_ROUTES) {
      const { unmount } = render(
        <AdmissionsCrmPage
          routeKey={route.key}
          userPermissions={fullPermissions}
          stateOverride={{
            tenantId: 23,
            leads: [
              {
                id: 11,
                tenant_id: 23,
                lead_ref: "L-11",
                status: "lead_created",
                full_name: "Lead One",
                email: "lead.one@example.edu",
                source_channel: "direct",
              },
            ],
            applicants: [
              {
                id: 12,
                tenant_id: 23,
                lead_id: 11,
                applicant_ref: "A-12",
                status: "applicant_created",
                full_name: "Applicant One",
                email: "app.one@example.edu",
              },
            ],
            applications: [
              {
                id: 13,
                tenant_id: 23,
                applicant_id: 12,
                application_ref: "APP-13",
                status: "application_started",
                program_code: "CS",
                intake_term: "2026-FALL",
              },
            ],
          }}
        />,
      );
      expect(screen.getByTestId(`acrm-page-${route.key}`)).toBeInTheDocument();
      unmount();
    }
  });

  it("shows permission denied state when required permissions missing", () => {
    render(<AdmissionsCrmPage routeKey="dashboard" userPermissions={[ADMISSIONS_CRM_RUNTIME_PERMISSIONS.WRITE]} />);
    expect(screen.getByTestId("acrm-permission-denied-state")).toBeInTheDocument();
  });
});
