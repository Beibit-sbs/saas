"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useAuth } from "./AuthProvider";
import { useLanguage } from "./LanguageProvider";

export default function SessionPanel() {
  const router = useRouter();
  const { user, logout } = useAuth();
  const { language } = useLanguage();
  const uiLang = language === "kk" || language === "en" ? language : "ru";

  const labels = {
    kk: {
      roles: "рөлдер",
      admin: "Админ",
      profile: "Профиль",
      logout: "Шығу",
      notLoggedIn: "Кіру орындалмаған",
      login: "Кіру",
    },
    ru: {
      roles: "роли",
      admin: "Админ",
      profile: "Профиль",
      logout: "Выйти",
      notLoggedIn: "Не выполнен вход",
      login: "Войти",
    },
    en: {
      roles: "roles",
      admin: "Admin",
      profile: "Profile",
      logout: "Logout",
      notLoggedIn: "Not logged in",
      login: "Login",
    },
  }[uiLang];

  const handleLogout = () => {
    logout();
    router.push("/login");
    router.refresh();
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 20,
        right: 20,
        zIndex: 1000,
        background: "white",
        border: "1px solid #d8dbe2",
        borderRadius: 10,
        padding: "8px 10px",
        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
        fontSize: 13,
        minWidth: 200,
      }}
    >
      {user ? (
        <>
          <div><b>{user.display_name}</b></div>
          <div style={{ color: "#555", marginTop: 2 }}>{user.user_id}</div>
          <div style={{ color: "#555", marginTop: 2 }}>{labels.roles}: {user.roles.join(", ")}</div>
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <Link href="/admin">{labels.admin}</Link>
            <Link href="/profile">{labels.profile}</Link>
            <button
              type="button"
              onClick={handleLogout}
              style={{ border: "none", background: "transparent", cursor: "pointer", padding: 0 }}
            >
              {labels.logout}
            </button>
          </div>
        </>
      ) : (
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
          <span>{labels.notLoggedIn}</span>
          <Link href="/login">{labels.login}</Link>
        </div>
      )}
    </div>
  );
}
