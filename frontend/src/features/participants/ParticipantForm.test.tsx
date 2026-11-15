import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { mockApi, renderWithProviders } from "../../test/utils";
import { ParticipantForm } from "./ParticipantForm";

vi.mock("react-leaflet", async () => (await import("../../test/leafletMock")).leafletMock);

afterEach(() => vi.unstubAllGlobals());

const TWO = {
  results: [
    { label: "Wrzeszcz, Gdańsk", lat: 54.3797, lon: 18.607 },
    { label: "Wrzeszcz Górny, Gdańsk", lat: 54.37, lon: 18.59 },
  ],
};

async function fillAndSubmit(start = "Wrzeszcz") {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Imię"), "Łukasz");
  await user.type(screen.getByLabelText("Skąd"), start);
  await user.click(screen.getByRole("radio", { name: "Rower" }));
  await user.click(screen.getByRole("button", { name: "Dodaj osobę" }));
  return user;
}

it("shows address choices when geocode returns several results", async () => {
  mockApi({ "POST /geocode": TWO });
  renderWithProviders(<ParticipantForm meetupId={1} />);
  await fillAndSubmit();
  expect(await screen.findByRole("radio", { name: "Wrzeszcz, Gdańsk" })).toBeInTheDocument();
  expect(screen.getByRole("radio", { name: "Wrzeszcz Górny, Gdańsk" })).toBeInTheDocument();
});

it("shows not-found error under start field", async () => {
  mockApi({ "POST /geocode": { results: [] } });
  renderWithProviders(<ParticipantForm meetupId={1} />);
  await fillAndSubmit("Atlantyda");
  expect(await screen.findByText("Nie znaleziono adresu — dopisz miasto")).toBeInTheDocument();
  expect(screen.getByLabelText("Skąd")).toHaveAttribute("aria-invalid", "true");
});

it("requires a travel mode", async () => {
  const calls = mockApi({ "POST /geocode": TWO });
  renderWithProviders(<ParticipantForm meetupId={1} />);
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Imię"), "Ola");
  await user.type(screen.getByLabelText("Skąd"), "Sopot");
  await user.click(screen.getByRole("button", { name: "Dodaj osobę" }));
  expect(screen.getByText("Wybierz środek transportu.")).toBeInTheDocument();
  expect(calls).toEqual([]);
});

it("saves participant with selected coordinates", async () => {
  const calls = mockApi({
    "POST /geocode": TWO,
    "POST /meetups/1/participants": () =>
      Response.json(
        { id: 5, name: "Łukasz", start_label: "Wrzeszcz", lat: 54.37, lon: 18.59, mode: "bike" },
        { status: 201 },
      ),
    "GET /meetups/1": { id: 1, participants: [] },
  });
  const onDone = vi.fn();
  renderWithProviders(<ParticipantForm meetupId={1} onDone={onDone} />);
  const user = await fillAndSubmit();
  await user.click(await screen.findByRole("radio", { name: "Wrzeszcz Górny, Gdańsk" }));
  await user.click(screen.getByRole("button", { name: "Zgadza się — zapisz" }));
  await waitFor(() => expect(onDone).toHaveBeenCalled());
  const post = calls.find((c) => c.path === "/meetups/1/participants");
  expect(post?.body).toEqual({
    name: "Łukasz",
    start_label: "Wrzeszcz",
    mode: "bike",
    lat: 54.37,
    lon: 18.59,
  });
});
