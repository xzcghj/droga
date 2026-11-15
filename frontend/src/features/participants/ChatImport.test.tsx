import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi, renderWithProviders } from "../../test/utils";
import { ChatImport } from "./ChatImport";

afterEach(() => vi.unstubAllGlobals());

const DRAFT = {
  participants: [
    {
      name: "Ola",
      start_label: "Gdynia",
      mode: "transit",
      note: null,
      lat: 54.52,
      lon: 18.53,
      geocode_error: false,
    },
    {
      name: "Kuba",
      start_label: "Oliwa",
      mode: "bike",
      note: "spóźni się",
      lat: 54.41,
      lon: 18.56,
      geocode_error: false,
    },
  ],
  unparsed: ["xD"],
};

const AI_ON = { ai_enabled: true, ai_provider: "gemini" };

async function parse(draft: unknown = DRAFT, extra: Record<string, unknown> = {}) {
  const calls = mockApi({ "GET /meta": AI_ON, "POST /ai/parse-participants": draft, ...extra });
  renderWithProviders(<ChatImport meetupId={1} />);
  const user = userEvent.setup();
  await user.click(await screen.findByRole("button", { name: "Wklej z czatu" }));
  await user.type(
    screen.getByLabelText("Wiadomość z czatu"),
    "Ola z Gdyni SKM, Kuba rowerem z Oliwy",
  );
  await user.click(screen.getByRole("button", { name: "Rozpoznaj" }));
  await screen.findByLabelText("Imię (wiersz 1)");
  return { user, calls };
}

it("hidden when AI disabled", async () => {
  const calls = mockApi({ "GET /meta": { ai_enabled: false, ai_provider: null } });
  const { client } = renderWithProviders(<ChatImport meetupId={1} />);
  await waitFor(() => expect(calls).toHaveLength(1));
  await waitFor(() => expect(client.getQueryData(["meta"])).toBeDefined());
  expect(screen.queryByRole("button", { name: "Wklej z czatu" })).not.toBeInTheDocument();
});

it("shows unparsed fragments and counter", async () => {
  await parse();
  expect(screen.getByText(/xD/)).toBeInTheDocument();
});

it("editing a row updates the draft", async () => {
  const { user } = await parse();
  const name = screen.getByLabelText("Imię (wiersz 1)");
  await user.clear(name);
  await user.type(name, "Aleksandra");
  expect(name).toHaveValue("Aleksandra");
});

it("removing a row decrements the button count", async () => {
  const { user } = await parse();
  expect(screen.getByRole("button", { name: "Dodaj 2 osoby" })).toBeEnabled();
  await user.click(screen.getByRole("button", { name: "Usuń wiersz 2" }));
  expect(screen.getByRole("button", { name: "Dodaj 1 osobę" })).toBeEnabled();
});

it("submit disabled while any row has geocode_error or missing mode", async () => {
  const draft = {
    participants: [
      { ...DRAFT.participants[0], mode: null },
      { ...DRAFT.participants[1], lat: null, lon: null, geocode_error: true },
    ],
    unparsed: [],
  };
  const { user } = await parse(draft, {
    "POST /geocode": { results: [{ label: "Oliwa, Gdańsk", lat: 54.41, lon: 18.56 }] },
  });
  const submit = screen.getByRole("button", { name: "Dodaj 2 osoby" });
  expect(submit).toBeDisabled();
  await user.selectOptions(screen.getByLabelText("Środek transportu (wiersz 1)"), "walk");
  expect(submit).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Szukaj adresu (wiersz 2)" }));
  await waitFor(() => expect(submit).toBeEnabled());
});

it("editing start of a located row requires a new search", async () => {
  const { user } = await parse();
  await user.type(screen.getByLabelText("Skąd (wiersz 1)"), " Orłowo");
  expect(screen.getByRole("button", { name: "Dodaj 2 osoby" })).toBeDisabled();
});

it("submits batch with edited values", async () => {
  const { user, calls } = await parse(DRAFT, {
    "POST /meetups/1/participants/batch": () => Response.json([], { status: 201 }),
    "GET /meetups/1": { id: 1, participants: [] },
    "GET /meetups": [],
  });
  const name = screen.getByLabelText("Imię (wiersz 1)");
  await user.clear(name);
  await user.type(name, "Ola K.");
  await user.selectOptions(screen.getByLabelText("Środek transportu (wiersz 2)"), "car");
  await user.click(screen.getByRole("button", { name: "Dodaj 2 osoby" }));
  await waitFor(() => expect(calls.some((c) => c.path.endsWith("/batch"))).toBe(true));
  const batch = calls.find((c) => c.path.endsWith("/batch"))!;
  expect(batch.body).toEqual({
    participants: [
      { name: "Ola K.", start_label: "Gdynia", mode: "transit", lat: 54.52, lon: 18.53 },
      { name: "Kuba", start_label: "Oliwa", mode: "car", lat: 54.41, lon: 18.56 },
    ],
  });
  await waitFor(() => expect(screen.queryByLabelText("Imię (wiersz 1)")).not.toBeInTheDocument());
});
