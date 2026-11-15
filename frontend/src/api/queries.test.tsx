import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, expect, it, vi } from "vitest";
import { SUGGESTIONS } from "../test/fixtures";
import { mockApi } from "../test/utils";
import { useAddParticipant, useSuggestions } from "./queries";

afterEach(() => vi.unstubAllGlobals());

it("ranking is keyed by line-up: a change shows no stale ranking and triggers no refetch", async () => {
  const calls = mockApi({
    "GET /meetups/1/suggestions": SUGGESTIONS,
    "POST /meetups/1/participants": () => Response.json({ id: 9 }, { status: 201 }),
    "GET /meetups/1": { id: 1 },
    "GET /meetups": [],
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
  const { result } = renderHook(
    () => {
      const [lineup, setLineup] = useState("A");
      return {
        setLineup,
        s: useSuggestions(1, lineup, lineup === "A"),
        add: useAddParticipant(1),
      };
    },
    { wrapper },
  );
  await waitFor(() => expect(result.current.s.data).toBeDefined());
  await act(async () => {
    await result.current.add.mutateAsync({
      name: "X",
      start_label: "Y",
      mode: "walk",
      lat: 1,
      lon: 2,
    });
    result.current.setLineup("B");
  });
  await new Promise((r) => setTimeout(r, 20));
  expect(result.current.s.data).toBeUndefined();
  expect(calls.filter((c) => c.path.startsWith("/meetups/1/suggestions"))).toHaveLength(1);
});
