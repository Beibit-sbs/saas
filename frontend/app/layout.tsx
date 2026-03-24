import type { Metadata } from "next";
import "./admin-console.css";

import { AuthProvider } from "./components/AuthProvider";
import HelpAssistant from "./components/HelpAssistant";
import { LanguageProvider } from "./components/LanguageProvider";
import LanguageSwitcher from "./components/LanguageSwitcher";
import SessionPanel from "./components/SessionPanel";

export const metadata: Metadata = {
  title: "AI Engineering Center",
  description: "Starter workspace for AI-assisted web system delivery",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body>
        <AuthProvider>
          <LanguageProvider>
            {children}
            <SessionPanel />
            <LanguageSwitcher />
            <HelpAssistant />
          </LanguageProvider>
        </AuthProvider>
      </body>
    </html>
  );
}