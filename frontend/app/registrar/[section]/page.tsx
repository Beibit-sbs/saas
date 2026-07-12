import Link from "next/link";
import { notFound } from "next/navigation";
import { REGISTRAR_NAV_ITEMS, REGISTRAR_SECTIONS, type RegistrarSectionKey } from "../sections";

type RegistrarSectionPageProps = {
  params: {
    section: string;
  };
};

function isRegistrarSectionKey(value: string): value is RegistrarSectionKey {
  return Object.prototype.hasOwnProperty.call(REGISTRAR_SECTIONS, value);
}

export default function RegistrarSectionPage({ params }: RegistrarSectionPageProps) {
  const sectionKey = params.section;
  if (!isRegistrarSectionKey(sectionKey)) {
    notFound();
  }

  const section = REGISTRAR_SECTIONS[sectionKey];
  const relatedLinks = REGISTRAR_NAV_ITEMS.filter((item) => item.href !== `/registrar/${sectionKey}` && item.href !== "/registrar").slice(0, 3);

  return (
    <main className="min-h-screen bg-transparent px-4 py-8 sm:px-6">
      <section className="mx-auto max-w-5xl space-y-6">
        <div className="overflow-hidden rounded-[28px] border border-border/70 bg-card/80 shadow-[0_24px_70px_rgba(15,23,42,0.08)] backdrop-blur">
          <div className="bg-[linear-gradient(135deg,rgba(8,145,178,0.12),rgba(15,23,42,0.02)_55%,rgba(249,115,22,0.08))] px-6 py-8 sm:px-8">
            <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-primary/80">
              Registrar Workspace
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-foreground">{section.title}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground sm:text-base">
              {section.subtitle}
            </p>
          </div>

          <div className="grid gap-4 px-6 py-6 sm:px-8 lg:grid-cols-[1.35fr_0.95fr]">
            <div className="rounded-3xl border border-border/70 bg-background/75 p-5 shadow-sm">
              <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                What you can do here
              </h2>
              <ul className="mt-4 space-y-3 text-sm leading-7 text-foreground">
                {section.bullets.map((bullet) => (
                  <li key={bullet} className="flex gap-3">
                    <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-4 rounded-3xl border border-border/70 bg-secondary/45 p-5 shadow-sm">
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                  Next actions
                </h2>
                <p className="mt-2 text-sm leading-7 text-foreground">
                  This registrar-safe route replaces previous links to restricted console pages and keeps the workflow inside the registrar zone.
                </p>
              </div>

              <div className="space-y-2">
                {relatedLinks.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center justify-between rounded-2xl border border-border/70 bg-card px-4 py-3 text-sm font-medium text-foreground transition hover:border-primary/35 hover:bg-accent"
                  >
                    <span>{item.label}</span>
                    <span className="text-xs uppercase tracking-[0.14em] text-muted-foreground">Open</span>
                  </Link>
                ))}
              </div>

              <Link
                href="/registrar"
                className="inline-flex rounded-full bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-[0_14px_28px_rgba(8,145,178,0.24)] transition hover:opacity-95"
              >
                Back to registrar home
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}