"use client";

import { useState, useEffect } from "react";
import { ToastProvider, ToastViewport, Toast, ToastTitle, ToastDescription, ToastClose } from "./toast";

interface ToastData {
  id: string;
  title?: string;
  description?: string;
  variant?: "default" | "destructive" | "success";
}

let toastCount = 0;
const listeners: Array<(toasts: ToastData[]) => void> = [];
let globalToasts: ToastData[] = [];

export function toast(data: Omit<ToastData, "id">) {
  const id = String(++toastCount);
  const newToast = { ...data, id };
  globalToasts = [...globalToasts, newToast];
  listeners.forEach((l) => l(globalToasts));
  setTimeout(() => {
    globalToasts = globalToasts.filter((t) => t.id !== id);
    listeners.forEach((l) => l(globalToasts));
  }, 5000);
}

export function Toaster() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  useEffect(() => {
    const listener = (ts: ToastData[]) => setToasts([...ts]);
    listeners.push(listener);
    return () => {
      const idx = listeners.indexOf(listener);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);

  return (
    <ToastProvider>
      {toasts.map((t) => (
        <Toast key={t.id} variant={t.variant}>
          {t.title && <ToastTitle>{t.title}</ToastTitle>}
          {t.description && <ToastDescription>{t.description}</ToastDescription>}
          <ToastClose />
        </Toast>
      ))}
      <ToastViewport />
    </ToastProvider>
  );
}
