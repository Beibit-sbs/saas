import Link from "next/link";

type RoleNavItem = {
  href: string;
  label: string;
};

type RoleZoneLayoutProps = {
  zoneTitle: string;
  navItems: RoleNavItem[];
  children: React.ReactNode;
};

export function RoleZoneLayout({ zoneTitle, navItems, children }: RoleZoneLayoutProps) {
  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      <header
        style={{
          borderBottom: "1px solid rgba(15,23,42,0.08)",
          background: "#ffffff",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ maxWidth: 1080, margin: "0 auto", padding: "0.85rem 1rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
            <div>
              <p style={{ margin: 0, fontSize: "0.74rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "#475569", fontWeight: 700 }}>
                Role Workspace
              </p>
              <h2 style={{ margin: "0.2rem 0 0", fontSize: "1.05rem", color: "#0f172a" }}>{zoneTitle}</h2>
            </div>
            <Link href="/console" style={{ color: "#0f172a", fontWeight: 700, textDecoration: "none" }}>
              Back to Console
            </Link>
          </div>
          <nav aria-label={`${zoneTitle} navigation`} style={{ marginTop: "0.7rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  textDecoration: "none",
                  color: "#0f172a",
                  border: "1px solid rgba(15,23,42,0.12)",
                  borderRadius: 999,
                  padding: "0.32rem 0.72rem",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  background: "#fff",
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      {children}
    </div>
  );
}
