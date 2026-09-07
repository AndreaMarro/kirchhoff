/* Stato d'interazione del banco: solo vista, mai verita' elettrica.
   Sincronizzato nell'hash dell'URL: un refresh non perde il passo. */
import { useCallback, useEffect, useState } from "react";
import { formatHash, parseHash } from "../session/stage.ts";
import type { WorkbenchHash } from "../session/stage.ts";

export interface Selection {
  exercise: string;
  step: number;
  frame: "before" | "after";
}

export function selectionFromHash(hash: string, fallbackExercise: string): Selection {
  const parsed = parseHash(hash);
  return {
    exercise: parsed.exercise ?? fallbackExercise,
    step: parsed.step ?? -1,
    frame: parsed.frame ?? "before",
  };
}

export function useSelection(exercises: string[]): [Selection, (s: Selection) => void] {
  const [selection, setSelection] = useState<Selection>(() => {
    const fallback = exercises[0] ?? "";
    return selectionFromHash(window.location.hash, fallback);
  });

  useEffect(() => {
    const onHash = (): void => {
      setSelection((prev) => {
        const next = selectionFromHash(window.location.hash, prev.exercise);
        return sameSelection(prev, next) ? prev : next;
      });
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const update = useCallback((next: Selection) => {
    setSelection(next);
    const hash: WorkbenchHash = { exercise: next.exercise, step: next.step, frame: next.frame };
    const text = formatHash(hash);
    if (window.location.hash !== text) window.location.hash = text;
  }, []);

  return [selection, update];
}

function sameSelection(a: Selection, b: Selection): boolean {
  return a.exercise === b.exercise && a.step === b.step && a.frame === b.frame;
}

export function useTheme(): ["dark" | "light", () => void] {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    const saved = window.localStorage.getItem("kf-theme");
    return saved === "light" || saved === "dark" ? saved : "dark";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("kf-theme", theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }, []);

  return [theme, toggle];
}
