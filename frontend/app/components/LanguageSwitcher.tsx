"use client";

import { useEffect, useState } from "react";

import { useLanguage } from "./LanguageProvider";

const selectableUiLanguages = new Set(["kk", "ru", "en"]);

export default function LanguageSwitcher() {
  const { language, setLanguage, supportedLanguages, t } = useLanguage();
  const [pendingLanguage, setPendingLanguage] = useState(language);

  useEffect(() => {
    setPendingLanguage(language);
  }, [language]);

  const hasChanges = pendingLanguage !== language;

  return (
    <label
      style={{
        position: "fixed",
        left: 20,
        bottom: 20,
        zIndex: 1000,
        background: "white",
        border: "1px solid #d8dbe2",
        borderRadius: 10,
        padding: "8px 10px",
        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
        fontSize: 13,
      }}
    >
      {t("ui.language")}: {" "}
      <select
        value={pendingLanguage}
        onChange={(e) => setPendingLanguage(e.target.value)}
        className="rounded-md border border-border px-1.5 py-0.5"
      >
        {supportedLanguages.filter((lang) => selectableUiLanguages.has(lang.code)).map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.native_name || lang.name || lang.code}
          </option>
        ))}
      </select>
      <button
        type="button"
        onClick={() => setLanguage(pendingLanguage)}
        disabled={!hasChanges}
        style={{
          marginLeft: 8,
          borderRadius: 6,
          border: "1px solid #1f6feb",
          padding: "2px 8px",
          cursor: hasChanges ? "pointer" : "not-allowed",
          background: hasChanges ? "#1f6feb" : "#e5e7eb",
          color: hasChanges ? "white" : "#6b7280",
        }}
      >
        {t("ui.apply")}
      </button>
    </label>
  );
}
