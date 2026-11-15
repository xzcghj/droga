import { Bike, Car, Footprints, TramFront, type LucideIcon } from "lucide-react";
import type { TravelMode, VenueCategory } from "../api/client";

export interface ModeInfo {
  label: string;
  /** Kolor wypełnienia (znacznik, pasek) — biały tekst na nim ma kontrast ≥ 4.5:1. */
  color: string;
  icon: LucideIcon;
}

export const MODES: Record<TravelMode, ModeInfo> = {
  walk: { label: "Pieszo", color: "#15803d", icon: Footprints },
  bike: { label: "Rower", color: "#b45309", icon: Bike },
  transit: { label: "Komunikacja", color: "#1d4ed8", icon: TramFront },
  car: { label: "Auto", color: "#7e22ce", icon: Car },
};

export const MODE_ORDER: TravelMode[] = ["walk", "bike", "transit", "car"];

export const CATEGORIES: Record<VenueCategory, string> = {
  cafe: "Kawiarnia",
  bar: "Bar / pub",
  restaurant: "Restauracja",
  park: "Park",
};
