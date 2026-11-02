export type Source = { url: string; author: string; license: string };
export type Entry = {
  id: string;
  kind: string;
  theme: string;
  latin: string;
  tifinagh: string;
  french: string;
  hint?: string;
  ipa?: string;
  sources: Source[];
  images?: Source[];
};
export type Progress = {
  content_id: string;
  correct: number;
  errors: number;
  streak: number;
  due: string;
};
