import Link from "next/link";

export default function ConsoleIntegrationsRootPage() {
  return (
    <main className="space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">Integrations</h1>
        <p className="text-sm text-muted-foreground">
          Manage identity federation and directory integrations.
        </p>
      </header>
      <section className="grid gap-3 sm:grid-cols-2">
        <Link
          href="/console/federation"
          className="rounded-lg border border-border p-4 hover:bg-muted/40"
        >
          <h2 className="font-medium">Identity Federation</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure SSO providers and federation settings.
          </p>
        </Link>
        <Link
          href="/console/ldap"
          className="rounded-lg border border-border p-4 hover:bg-muted/40"
        >
          <h2 className="font-medium">LDAP</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Configure directory sync and LDAP connectivity.
          </p>
        </Link>
      </section>
    </main>
  );
}
