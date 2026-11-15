import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { meetupFixture, PEOPLE, SUGGESTIONS } from "../../test/fixtures";
import { mockApi, renderWithProviders } from "../../test/utils";
import { SuggestionsPanel } from "./SuggestionsPanel";

afterEach(() => vi.unstubAllGlobals());

it("find button disabled under two participants", () => {
  mockApi({});
  renderWithProviders(
    <SuggestionsPanel
      meetup={meetupFixture({ participants: [PEOPLE[0]!] })}
      onHighlight={() => {}}
    />,
  );
  expect(screen.getByRole("button", { name: "Znajdź miejsce" })).toBeDisabled();
  expect(screen.getByText("Dodaj co najmniej 2 osoby")).toBeInTheDocument();
});

it("lists candidates after clicking find and highlights on hover", async () => {
  mockApi({ "GET /meetups/1/suggestions": SUGGESTIONS });
  const onHighlight = vi.fn();
  renderWithProviders(<SuggestionsPanel meetup={meetupFixture()} onHighlight={onHighlight} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Znajdź miejsce" }));
  expect(await screen.findByText("Kawiarnia Łąka")).toBeInTheDocument();
  expect(screen.getAllByText("Różnica: 10 min")).toHaveLength(2);
  await user.hover(screen.getByText("Bistro B"));
  expect(onHighlight).toHaveBeenLastCalledWith("way/2");
});

it("choosing a card patches chosen_venue", async () => {
  const calls = mockApi({
    "GET /meetups/1/suggestions": SUGGESTIONS,
    "PATCH /meetups/1": meetupFixture(),
    "GET /meetups": [],
  });
  renderWithProviders(<SuggestionsPanel meetup={meetupFixture()} onHighlight={() => {}} />);
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Znajdź miejsce" }));
  await user.click(await screen.findByRole("button", { name: "Wybierz: Bistro B" }));
  await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
  expect(calls.find((c) => c.method === "PATCH")!.body).toEqual({
    chosen_venue: { name: "Bistro B", lat: 54.45, lon: 18.55, osm_id: "way/2" },
  });
});

it("snapshot source shows notice", async () => {
  mockApi({ "GET /meetups/1/suggestions": { ...SUGGESTIONS, venue_source: "snapshot" } });
  renderWithProviders(<SuggestionsPanel meetup={meetupFixture()} onHighlight={() => {}} />);
  await userEvent.setup().click(screen.getByRole("button", { name: "Znajdź miejsce" }));
  expect(
    await screen.findByText("Lista lokali z zapisanej bazy (usługa mapowa niedostępna)"),
  ).toBeInTheDocument();
});

it("empty list shows hint", async () => {
  mockApi({ "GET /meetups/1/suggestions": { venue_source: "overpass", candidates: [] } });
  renderWithProviders(<SuggestionsPanel meetup={meetupFixture()} onHighlight={() => {}} />);
  await userEvent.setup().click(screen.getByRole("button", { name: "Znajdź miejsce" }));
  expect(
    await screen.findByText("Brak lokali tego typu w okolicy — spróbuj innej kategorii"),
  ).toBeInTheDocument();
});
