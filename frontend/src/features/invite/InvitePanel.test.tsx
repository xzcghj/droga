import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { meetupFixture } from "../../test/fixtures";
import { mockApi, renderWithProviders } from "../../test/utils";
import { InvitePanel } from "./InvitePanel";

afterEach(() => vi.unstubAllGlobals());

const CHOSEN = { name: "Kawiarnia Łąka", lat: 54.44, lon: 18.56, osm_id: "node/1" };

it("is hidden until a venue is chosen", () => {
  mockApi({});
  renderWithProviders(<InvitePanel meetup={meetupFixture()} />);
  expect(screen.queryByRole("button", { name: "Napisz zaproszenie" })).not.toBeInTheDocument();
});

it("generates and shows source label", async () => {
  mockApi({ "POST /meetups/1/invite": { message: "Hej! Widzimy się o 18:00.", source: "ai" } });
  renderWithProviders(<InvitePanel meetup={meetupFixture({ chosen_venue: CHOSEN })} />);
  await userEvent.setup().click(screen.getByRole("button", { name: "Napisz zaproszenie" }));
  expect(await screen.findByLabelText("Treść zaproszenia")).toHaveValue(
    "Hej! Widzimy się o 18:00.",
  );
  expect(screen.getByText("napisane przez AI")).toBeInTheDocument();
});

it("shows saved invite immediately", () => {
  mockApi({});
  renderWithProviders(
    <InvitePanel meetup={meetupFixture({ chosen_venue: CHOSEN, invite_message: "Zapisane" })} />,
  );
  expect(screen.getByLabelText("Treść zaproszenia")).toHaveValue("Zapisane");
});

it("copy writes to clipboard", async () => {
  const user = userEvent.setup();
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
  mockApi({ "POST /meetups/1/invite": { message: "Tekst z szablonu", source: "template" } });
  renderWithProviders(<InvitePanel meetup={meetupFixture({ chosen_venue: CHOSEN })} />);
  await user.click(screen.getByRole("button", { name: "Napisz zaproszenie" }));
  expect(await screen.findByText("z szablonu")).toBeInTheDocument();
  const box = screen.getByLabelText("Treść zaproszenia");
  await user.type(box, "!");
  await user.click(screen.getByRole("button", { name: "Kopiuj" }));
  expect(writeText).toHaveBeenCalledWith("Tekst z szablonu!");
  expect(await screen.findByText("Skopiowano")).toBeInTheDocument();
});

it("save patches invite_message", async () => {
  const calls = mockApi({
    "POST /meetups/1/invite": { message: "Hej", source: "template" },
    "PATCH /meetups/1": meetupFixture({ chosen_venue: CHOSEN, invite_message: "Hej" }),
    "GET /meetups": [],
  });
  const user = userEvent.setup();
  renderWithProviders(<InvitePanel meetup={meetupFixture({ chosen_venue: CHOSEN })} />);
  await user.click(screen.getByRole("button", { name: "Napisz zaproszenie" }));
  await screen.findByLabelText("Treść zaproszenia");
  await user.click(screen.getByRole("button", { name: "Zapisz" }));
  await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
  expect(calls.find((c) => c.method === "PATCH")!.body).toEqual({ invite_message: "Hej" });
});
