"use client";

import { useState, type ReactNode } from "react";

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from "./alert-dialog";
import { cn } from "../utils/cn";
import { buttonVariants } from "./button";

interface ConfirmActionDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void | Promise<void>;
  variant?: "default" | "destructive";
  loading?: boolean;
  trigger?: ReactNode;
}

export function ConfirmActionDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  onConfirm,
  variant = "default",
  loading,
  trigger,
}: ConfirmActionDialogProps) {
  const [innerOpen, setInnerOpen] = useState(false);
  const resolvedOpen = open ?? innerOpen;
  const resolvedOnOpenChange = onOpenChange ?? setInnerOpen;

  return (
    <AlertDialog open={resolvedOpen} onOpenChange={resolvedOnOpenChange}>
      {trigger ? <div onClick={() => resolvedOnOpenChange(true)}>{trigger}</div> : null}
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && <AlertDialogDescription>{description}</AlertDialogDescription>}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>{cancelLabel}</AlertDialogCancel>
          <AlertDialogAction
            onClick={async () => {
              await onConfirm();
              resolvedOnOpenChange(false);
            }}
            disabled={loading}
            className={cn(
              variant === "destructive" && buttonVariants({ variant: "destructive" }),
            )}
          >
            {loading ? "Processing…" : confirmLabel}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
