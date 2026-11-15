import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { PEOPLE, SUGGESTIONS } from "../../test/fixtures";
import { FairnessBar } from "./FairnessBar";

const travel = SUGGESTIONS.candidates[0]!.travel;

it("bar widths proportional to max", () => {
  render(<FairnessBar travel={travel} participants={PEOPLE} maxMinutes={20} />);
  expect(screen.getByTestId("bar-1")).toHaveStyle({ width: "100%" });
  expect(screen.getByTestId("bar-2")).toHaveStyle({ width: "50%" });
});

it("zero max does not divide by zero", () => {
  const zero = travel.map((t) => ({ ...t, minutes: 0 }));
  render(<FairnessBar travel={zero} participants={PEOPLE} maxMinutes={0} />);
  expect(screen.getByTestId("bar-1")).toHaveStyle({ width: "0%" });
});

it("estimate rows show ≈", () => {
  render(<FairnessBar travel={travel} participants={PEOPLE} maxMinutes={20} />);
  expect(screen.getByText("≈ 20 min")).toBeInTheDocument();
  expect(screen.getByText("10 min")).toBeInTheDocument();
  expect(screen.getByText("Ola")).toBeInTheDocument();
});
