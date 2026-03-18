"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuth } from "../components/AuthProvider";
import { useLanguage } from "../components/LanguageProvider";

export default function ProfilePage() {
  const { user } = useAuth();
  const { language, supportedLanguages, setLanguage } = useLanguage();
  const [pendingLanguage, setPendingLanguage] = useState(language);
  const uiLang = language === "kk" || language === "en" ? language : "ru";

  const labels = {
    kk: {
      title: "Пайдаланушы профилі",
      name: "Аты",
      userId: "User ID",
      roles: "Рөлдер",
      currentLanguage: "Ағымдағы тіл",
      pickLanguage: "Аккаунт тілін таңда",
      apply: "Тілді қолдану",
      note: "Мұнда тіл өзгерісі пайдаланушы профиліне сақталады және кіргеннен кейін автоматты жүктеледі.",
      notLoggedIn: "Кіру орындалмаған. Өтіңіз",
    },
    ru: {
      title: "Профиль пользователя",
      name: "Имя",
      userId: "User ID",
      roles: "Роли",
      currentLanguage: "Текущий язык",
      pickLanguage: "Выбери язык аккаунта",
      apply: "Применить язык",
      note: "Изменение языка здесь сохранится в профиль пользователя и будет подгружаться после входа.",
      notLoggedIn: "Вход не выполнен. Перейди на",
    },
    en: {
      title: "User Profile",
      name: "Name",
      userId: "User ID",
      roles: "Roles",
      currentLanguage: "Current language",
      pickLanguage: "Choose account language",
      apply: "Apply language",
      note: "Language changes here are saved to the user profile and loaded automatically after login.",
      notLoggedIn: "You are not logged in. Go to",
    },
  }[uiLang];

  useEffect(() => {
    setPendingLanguage(language);
  }, [language]);

  const hasChanges = pendingLanguage !== language;

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24, maxWidth: 820, margin: "0 auto" }}>
      <h1>{labels.title}</h1>
      {user ? (
        <>
          <p><b>{labels.name}:</b> {user.display_name}</p>
          <p><b>{labels.userId}:</b> {user.user_id}</p>
          <p><b>{labels.roles}:</b> {user.roles.join(", ")}</p>
          <p><b>{labels.currentLanguage}:</b> {language}</p>
          <label style={{ display: "block", marginTop: 16 }}>
            {labels.pickLanguage}:
            <select
              value={pendingLanguage}
              onChange={(e) => setPendingLanguage(e.target.value)}
              style={{ display: "block", marginTop: 8, padding: 8, minWidth: 280 }}
            >
              {supportedLanguages.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.native_name} ({item.code})
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => setLanguage(pendingLanguage)}
            disabled={!hasChanges}
            style={{
              marginTop: 12,
              padding: "8px 14px",
              borderRadius: 8,
              border: "1px solid #1f6feb",
              background: hasChanges ? "#1f6feb" : "#e5e7eb",
              color: hasChanges ? "#fff" : "#6b7280",
              cursor: hasChanges ? "pointer" : "not-allowed",
            }}
          >
            {labels.apply}
          </button>
          <p style={{ color: "#555" }}>
            {labels.note}
          </p>
        </>
      ) : (
        <p>
          {labels.notLoggedIn} <Link href="/login">/login</Link>.
        </p>
      )}
    </main>
  );
}
