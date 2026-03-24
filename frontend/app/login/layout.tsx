import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "EduAdmin Console",
  description: "Sign in to the EduAdmin administration console",
};

export default function LoginLayout({ children }: { children: ReactNode }) {
  return children;
}
