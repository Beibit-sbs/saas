import { en } from "./en";
import { kk } from "./kk";
import { ru } from "./ru";

export const commonTranslations = {
  ru,
  en,
  kk,
} as const;

export type CommonTranslationKey = keyof typeof ru;
export type CommonTranslationDictionary = Record<CommonTranslationKey, string>;

const _enCheck: CommonTranslationDictionary = en;
const _kkCheck: CommonTranslationDictionary = kk;
void _enCheck;
void _kkCheck;
