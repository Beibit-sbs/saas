"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../components/AuthProvider";
import { useLanguage } from "../components/LanguageProvider";

type DemoUser = {
  user_id: string;
  display_name: string;
  roles: string[];
  default_language: string;
};

type AuthModesResponse = {
  modes: {
    local: boolean;
    ldap: boolean;
    api_keys: boolean;
  };
};

export default function LoginPage() {
  const router = useRouter();
  const { loginDemo, loginWithCredentials, loginWithLdap, user } = useAuth();
  const { language } = useLanguage();
  const [users, setUsers] = useState<DemoUser[]>([]);
  const [authModes, setAuthModes] = useState<AuthModesResponse["modes"] | null>(null);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [loginValue, setLoginValue] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [status, setStatus] = useState<string | null>(null);
  const uiLang = language === "kk" || language === "en" ? language : "ru";

  const labels = {
    kk: {
      loadUsersError: "Пайдаланушыларды жүктеу қатесі",
      pickUser: "Пайдаланушыны таңда.",
      loginError: "Кіру қатесі",
      title: "Демо кіру",
      subtitle: "Жеке тіл мен рөлдердің интерфейсте қалай жұмыс істейтінін көру үшін тест пайдаланушысын таңда немесе mock login/password қолдан.",
      byDemo: "Demo-пайдаланушы арқылы кіру",
      login: "Кіру",
      byCredentials: "Mock login/password",
      byLdap: "LDAP/AD арқылы кіру",
      loginPlaceholder: "login",
      passwordPlaceholder: "password",
      loginByCredentials: "Логин/құпия сөзбен кіру",
      loginByLdap: "LDAP/AD арқылы кіру",
      testPairs: "Тест жұптары: admin/admin123, teacher/teacher123, student/student123",
    },
    ru: {
      loadUsersError: "Ошибка загрузки пользователей",
      pickUser: "Выбери пользователя.",
      loginError: "Ошибка входа",
      title: "Демо-вход",
      subtitle: "Выбери тестового пользователя или выполни mock login/password, чтобы посмотреть персональный язык и роли в интерфейсе.",
      byDemo: "Вход по demo-пользователю",
      login: "Войти",
      byCredentials: "Mock login/password",
      byLdap: "Вход через LDAP/AD",
      loginPlaceholder: "login",
      passwordPlaceholder: "password",
      loginByCredentials: "Войти по логину/паролю",
      loginByLdap: "Войти через LDAP/AD",
      testPairs: "Тестовые пары: admin/admin123, teacher/teacher123, student/student123",
    },
    en: {
      loadUsersError: "Failed to load users",
      pickUser: "Select a user.",
      loginError: "Login error",
      title: "Demo Login",
      subtitle: "Select a test user or use mock login/password to see personal language and roles in the UI.",
      byDemo: "Login by demo user",
      login: "Login",
      byCredentials: "Mock login/password",
      byLdap: "LDAP/AD login",
      loginPlaceholder: "login",
      passwordPlaceholder: "password",
      loginByCredentials: "Login with credentials",
      loginByLdap: "Login via LDAP/AD",
      testPairs: "Test pairs: admin/admin123, teacher/teacher123, student/student123",
    },
  }[uiLang];

  useEffect(() => {
    if (user) {
      router.push("/");
      return;
    }

    const loadUsers = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
        const [usersRes, modesRes] = await Promise.all([
          fetch(`${baseUrl}/auth/demo-users`, { cache: "no-store" }),
          fetch(`${baseUrl}/auth/modes`, { cache: "no-store" }),
        ]);
        if (!usersRes.ok) {
          setStatus(`${labels.loadUsersError}: ${usersRes.status}`);
          return;
        }
        const json = (await usersRes.json()) as { users: DemoUser[] };
        setUsers(json.users);
        if (json.users.length > 0) {
          setSelectedUserId(json.users[0].user_id);
        }

        if (modesRes.ok) {
          const modesJson = (await modesRes.json()) as AuthModesResponse;
          setAuthModes(modesJson.modes);
        }
      } catch (error) {
        setStatus(String(error));
      }
    };

    void loadUsers();
  }, [router, user, labels.loadUsersError]);

  const loginByDemoUser = async () => {
    if (!selectedUserId) {
      setStatus(labels.pickUser);
      return;
    }

    const result = await loginDemo(selectedUserId);
    if (!result.ok) {
      setStatus(result.error || labels.loginError);
      return;
    }

    router.push("/");
    router.refresh();
  };

  const loginByCredentials = async () => {
    setStatus(null);
    const result = await loginWithCredentials(loginValue, password);
    if (!result.ok) {
      setStatus(result.error || labels.loginError);
      return;
    }

    router.push("/");
    router.refresh();
  };

  const loginByLdap = async () => {
    setStatus(null);
    const result = await loginWithLdap(loginValue, password);
    if (!result.ok) {
      setStatus(result.error || labels.loginError);
      return;
    }

    router.push("/");
    router.refresh();
  };

  return (
    <main style={{ fontFamily: "sans-serif", padding: 24, maxWidth: 720, margin: "0 auto" }}>
      <h1>{labels.title}</h1>
      <p>{labels.subtitle}</p>

      <div style={{ display: "grid", gap: 24, gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))" }}>
        <section style={{ border: "1px solid #eceef3", borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>{labels.byDemo}</h2>
          <div style={{ display: "grid", gap: 10 }}>
            <select value={selectedUserId} onChange={(e) => setSelectedUserId(e.target.value)}>
              {users.map((item) => (
                <option key={item.user_id} value={item.user_id}>
                  {item.display_name} ({item.user_id}) - {item.default_language}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={loginByDemoUser}
              style={{ width: 180, borderRadius: 8, border: "none", padding: "8px 12px", background: "#111827", color: "#fff" }}
            >
              {labels.login}
            </button>
          </div>
        </section>

        <section style={{ border: "1px solid #eceef3", borderRadius: 12, padding: 16 }}>
          <h2 style={{ marginTop: 0 }}>{labels.byCredentials}</h2>
          <div style={{ display: "grid", gap: 10 }}>
            <input value={loginValue} onChange={(e) => setLoginValue(e.target.value)} placeholder={labels.loginPlaceholder} />
            <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder={labels.passwordPlaceholder} type="password" />
            <button
              type="button"
              onClick={loginByCredentials}
              style={{ width: 220, borderRadius: 8, border: "none", padding: "8px 12px", background: "#111827", color: "#fff" }}
            >
              {labels.loginByCredentials}
            </button>
            <div style={{ fontSize: 13, color: "#555" }}>
              {labels.testPairs}
            </div>
          </div>
        </section>

        {authModes?.ldap ? (
          <section style={{ border: "1px solid #eceef3", borderRadius: 12, padding: 16 }}>
            <h2 style={{ marginTop: 0 }}>{labels.byLdap}</h2>
            <div style={{ display: "grid", gap: 10 }}>
              <input value={loginValue} onChange={(e) => setLoginValue(e.target.value)} placeholder={labels.loginPlaceholder} />
              <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder={labels.passwordPlaceholder} type="password" />
              <button
                type="button"
                onClick={loginByLdap}
                style={{ width: 220, borderRadius: 8, border: "none", padding: "8px 12px", background: "#0f766e", color: "#fff" }}
              >
                {labels.loginByLdap}
              </button>
            </div>
          </section>
        ) : null}
      </div>

      {status ? <p style={{ marginTop: 16 }}>{status}</p> : null}
    </main>
  );
}
