import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { ToastProvider } from "../components/ui/Toast";

export function renderWithProviders(ui: ReactElement, { route = "/" } = {}) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return {
    client,
    ...render(
      <QueryClientProvider client={client}>
        <ToastProvider>
          <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
        </ToastProvider>
      </QueryClientProvider>,
    ),
  };
}

type Handler = (url: string, init: RequestInit) => Response | Promise<Response>;

/** Atrapa fetch: routing po „METODA ścieżka” (bez prefiksu API). Zapisuje wywołania. */
export function mockApi(routes: Record<string, Handler | unknown>) {
  const calls: Array<{ method: string; path: string; body: unknown }> = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const path = url.replace(/^https?:\/\/[^/]+\/api\/v1/, "");
    const method = (init.method ?? "GET").toUpperCase();
    const body = typeof init.body === "string" ? JSON.parse(init.body) : undefined;
    calls.push({ method, path, body });
    const key = `${method} ${path.split("?")[0]}`;
    const handler = routes[key];
    if (handler === undefined) throw new Error(`Brak atrapy dla ${key}`);
    if (typeof handler === "function") return (handler as Handler)(url, init);
    return Response.json(handler);
  });
  vi.stubGlobal("fetch", fetchMock);
  return calls;
}

export const errorResponse = (
  status: number,
  code: string,
  message: string,
  details: unknown = null,
) => Response.json({ error: { code, message, details } }, { status });
