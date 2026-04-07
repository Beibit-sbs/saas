"use client";

import { useState } from "react";

import { buildCsrfHeaders } from "./csrf";
import { useLanguage } from "./LanguageProvider";

type HelpResponse = {
  answer: string;
  next_steps: string[];
  context: { page: string; field: string | null };
};

const fieldLabelStyle = { display: "block", fontSize: 13, marginBottom: 6 } as const;
const fieldInputStyle = { width: "100%", padding: 8, borderRadius: 8, border: "1px solid #c7ccd6" } as const;

export default function HelpAssistant() {
  const { t, language } = useLanguage();
  const [open, setOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [field, setField] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<HelpResponse | null>(null);

  const page =
    typeof window !== "undefined" && window.location.pathname.startsWith("/console/platform")
      ? "admin"
      : "general";
  const uiLang = language === "kk" || language === "en" ? language : "ru";

  const labels = {
    kk: {
      openAria: "AI-анықтаманы ашу",
      title: "AI-анықтама",
      serverError: "Сервер қатесі",
      fieldPlaceholder: "мысалы, ldap_bind_dn",
      questionPlaceholder: "Мұнда нені және қалай дұрыс толтыру керек?",
      answer: "Жауап",
      nextSteps: "Келесі қадамдар",
    },
    ru: {
      openAria: "Открыть AI-справочник",
      title: "AI-справочник",
      serverError: "Ошибка сервера",
      fieldPlaceholder: "например, ldap_bind_dn",
      questionPlaceholder: "Что тут нужно заполнить и как правильно?",
      answer: "Ответ",
      nextSteps: "Что делать дальше",
    },
    en: {
      openAria: "Open AI help",
      title: "AI help",
      serverError: "Server error",
      fieldPlaceholder: "e.g. ldap_bind_dn",
      questionPlaceholder: "What should be filled here and how?",
      answer: "Answer",
      nextSteps: "Next steps",
    },
  }[uiLang];

  const ask = async () => {
    if (!question.trim()) {
      setError(t("help.error.empty"));
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
      const csrfHeaders = await buildCsrfHeaders(baseUrl);
      const res = await fetch(`${baseUrl}/help/ask`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", ...csrfHeaders },
        body: JSON.stringify({
          language,
          page,
          question,
          field: field || null,
        }),
      });

      if (!res.ok) {
        setError(`${labels.serverError}: ${res.status}`);
        return;
      }

      const json = (await res.json()) as HelpResponse;
      setResponse(json);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        style={{
          position: "fixed",
          right: 20,
          bottom: 20,
          width: 56,
          height: 56,
          borderRadius: 999,
          border: "none",
          background: "#0b57d0",
          color: "white",
          fontSize: 22,
          cursor: "pointer",
          boxShadow: "0 8px 24px rgba(0,0,0,0.24)",
          zIndex: 1000,
        }}
        aria-label={labels.openAria}
        title={labels.title}
      >
        ?
      </button>

      {open ? (
        <section
          style={{
            position: "fixed",
            right: 20,
            bottom: 86,
            width: 360,
            maxWidth: "calc(100vw - 24px)",
            background: "white",
            border: "1px solid #d8dbe2",
            borderRadius: 12,
            padding: 14,
            boxShadow: "0 16px 40px rgba(0,0,0,0.22)",
            zIndex: 1000,
          }}
        >
          <h3 style={{ marginTop: 0, marginBottom: 8 }}>{t("help.title")}</h3>
          <p style={{ marginTop: 0, color: "#444", fontSize: 14 }}>
            {t("help.page")}: <b>{page}</b>
          </p>

          <label style={fieldLabelStyle}>{t("help.field")}</label>
          <input
            value={field}
            onChange={(e) => setField(e.target.value)}
            placeholder={labels.fieldPlaceholder}
            style={{ ...fieldInputStyle, marginBottom: 8 }}
          />

          <label style={fieldLabelStyle}>{t("help.question")}</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={4}
            placeholder={labels.questionPlaceholder}
            style={fieldInputStyle}
          />

          <button
            type="button"
            onClick={ask}
            disabled={loading}
            style={{
              marginTop: 10,
              border: "none",
              borderRadius: 8,
              background: "#111827",
              color: "white",
              padding: "8px 12px",
              cursor: "pointer",
            }}
          >
            {loading ? t("help.thinking") : t("help.ask")}
          </button>

          {error ? <p style={{ color: "#b00020", marginBottom: 0 }}>{error}</p> : null}

          {response ? (
            <div style={{ marginTop: 10, borderTop: "1px solid #eceef3", paddingTop: 8 }}>
              <p style={{ margin: "6px 0" }}><b>{labels.answer}:</b> {response.answer}</p>
              <p style={{ margin: "6px 0" }}><b>{labels.nextSteps}:</b></p>
              <ul style={{ marginTop: 0, paddingLeft: 20 }}>
                {response.next_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </>
  );
}
