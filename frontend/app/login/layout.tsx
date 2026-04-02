import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "AI University Console",
  description: "Sign in to the AI University Console",
};

export default function LoginLayout({ children }: { children: ReactNode }) {
  return children;
}
