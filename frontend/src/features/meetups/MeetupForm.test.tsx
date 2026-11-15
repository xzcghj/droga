import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { warsawLocalToIso } from "../../lib/format";
import { errorResponse, mockApi, renderWithProviders } from "../../test/utils";
import { MeetupForm } from "./MeetupForm";

afterEach(() => vi.unstubAllGlobals());

async function fill(title: string) {
  const user = userEvent.setup();
  await user.type(screen.getByLabelText("Nazwa"), title);
  const when = screen.getByLabelText("Data i godzina");
  await user.clear(when);
  await user.type(when, "2026-11-21T18:00");
  await user.click(screen.getByLabelText("Kawiarnia"));
  await user.click(screen.getByRole("button", { name: "Utwórz spotkanie" }));
}

it("shows field error from 422 under title", async () => {
  mockApi({
    "POST /meetups": () =>
      errorResponse(422, "validation_error", "Niepoprawne dane wejściowe.", [
        { field: "title", message: "Za długa nazwa" },
      ]),
  });
  const onCreated = vi.fn();
  renderWithProviders(<MeetupForm onCreated={onCreated} />);
  await fill("Kawa");
  expect(await screen.findByText("Za długa nazwa")).toBeInTheDocument();
  expect(screen.getByLabelText("Nazwa")).toHaveAttribute("aria-invalid", "true");
  expect(onCreated).not.toHaveBeenCalled();
});

it("sends scheduled_at with timezone offset", async () => {
  const calls = mockApi({ "POST /meetups": { id: 42 } });
  const onCreated = vi.fn();
  renderWithProviders(<MeetupForm onCreated={onCreated} />);
  await fill("Kawa w Łodzi");
  await waitFor(() => expect(onCreated).toHaveBeenCalledWith(42));
  expect(calls[0]!.body).toEqual({
    title: "Kawa w Łodzi",
    scheduled_at: "2026-11-21T18:00:00+01:00",
    venue_category: "cafe",
  });
});

it("uses summer offset for July dates", () => {
  expect(warsawLocalToIso("2026-07-11T18:00")).toBe("2026-07-11T18:00:00+02:00");
  expect(warsawLocalToIso("2026-03-29T03:30")).toBe("2026-03-29T03:30:00+02:00");
});
