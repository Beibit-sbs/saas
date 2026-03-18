"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { useLanguage } from "./components/LanguageProvider";
import { useAuth } from "./components/AuthProvider";

type MetaPayload = Record<string, unknown>;

export default function Page() {
  const { t, language } = useLanguage();
  const { user } = useAuth();
  const [meta, setMeta] = useState<MetaPayload | null>(null);
  const uiLang = language === "kk" || language === "en" ? language : "ru";

  const labels = {
    kk: {
      currentLanguage: "Ағымдағы тіл",
      loggedInAs: "Кірген қолданушы",
      notLoggedIn: "Кіру орындалмаған. Demo-пайдаланушы таңдау үшін",
      goToLogin: "бетіне өтіңіз.",
    },
    ru: {
      currentLanguage: "Текущий язык",
      loggedInAs: "Выполнен вход как",
      notLoggedIn: "Вход не выполнен. Перейди на",
      goToLogin: ", чтобы выбрать demo-пользователя.",
    },
    en: {
      currentLanguage: "Current language",
      loggedInAs: "Logged in as",
      notLoggedIn: "You are not logged in. Go to",
      goToLogin: "to choose a demo user.",
    },
  }[uiLang];

  useEffect(() => {
    const load = async () => {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost/api";
      try {
        const res = await fetch(`${baseUrl}/meta`, { cache: "no-store" });
        if (!res.ok) {
          setMeta({ error: `Backend returned ${res.status}` });
          return;
        }
        const json = (await res.json()) as MetaPayload;
        setMeta(json);
      } catch (error) {
        setMeta({ error: String(error) });
      }
    };

    void load();
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24, maxWidth: 920, margin: "0 auto" }}>
      <h1>{t("home.title")}</h1>
      <p>{t("home.subtitle")}</p>
      <p style={{ color: "#555" }}>{labels.currentLanguage}: <b>{language}</b></p>
      <p style={{ color: "#555" }}>
        {user ? (
          <>{labels.loggedInAs} <b>{user.display_name}</b> ({user.user_id}).</>
        ) : (
          <>{labels.notLoggedIn} <Link href="/login">/login</Link> {labels.goToLogin}</>
        )}
      </p>
      <pre style={{ background: "#f3f3f3", padding: 16, borderRadius: 8, overflowX: "auto" }}>
        {JSON.stringify(meta, null, 2)}
      </pre>
    </main>
  );
}
