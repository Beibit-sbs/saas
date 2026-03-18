import { en } from "./en";
import { kk } from "./kk";
import { ru } from "./ru";

export const adminTranslations = {
  ru,
  en,
  kk,
} as const;

export type AdminTranslationKey = keyof typeof ru;
export type AdminTranslationDictionary = Record<AdminTranslationKey, string>;

const _enCheck: AdminTranslationDictionary = en;
const _kkCheck: AdminTranslationDictionary = kk;
void _enCheck;
void _kkCheck;
