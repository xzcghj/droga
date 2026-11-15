import type { components } from "./schema";

type S = components["schemas"];
export type MeetupRead = S["MeetupRead"];
export type MeetupSummary = S["MeetupSummary"];
export type MeetupCreate = S["MeetupCreate"];
export type MeetupUpdate = S["MeetupUpdate"];
export type ParticipantRead = S["ParticipantRead"];
export type ParticipantCreate = S["ParticipantCreate"];
export type ParticipantUpdate = S["ParticipantUpdate"];
export type SuggestionsRead = S["SuggestionsRead"];
export type CandidateRead = S["CandidateRead"];
export type TravelRead = S["TravelRead"];
export type ChosenVenue = S["ChosenVenue"];
export type ParticipantDraft = S["ParticipantDraft"];
export type DraftParticipant = S["DraftParticipant"];
export type InviteRead = S["InviteRead"];
export type MetaRead = S["MetaRead"];
export type GeocodeMatch = S["GeocodeMatch"];
export type GeocodeResponse = S["GeocodeResponse"];
export type TravelMode = S["TravelMode"];
export type VenueCategory = S["VenueCategory"];

export const API_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const NETWORK_MESSAGE = "Brak połączenia z serwerem.";

function networkError(): ApiError {
  return new ApiError(0, "network_error", NETWORK_MESSAGE);
}

function isErrorBody(
  body: unknown,
): body is { error: { code: string; message: string; details: unknown } } {
  if (typeof body !== "object" || body === null || !("error" in body)) return false;
  const e = (body as { error: unknown }).error;
  return (
    typeof e === "object" &&
    e !== null &&
    typeof (e as { code?: unknown }).code === "string" &&
    typeof (e as { message?: unknown }).message === "string"
  );
}

export async function api<T>(
  path: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, headers, ...rest } = init;
  const h = new Headers(headers);
  h.set("Accept", "application/json");
  if (json !== undefined) h.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...rest,
      headers: h,
      body: json !== undefined ? JSON.stringify(json) : rest.body,
    });
  } catch {
    throw networkError();
  }

  if (response.status === 204) return undefined as T;

  let body: unknown;
  try {
    body = await response.json();
  } catch {
    throw networkError();
  }
  if (response.ok) return body as T;
  if (isErrorBody(body)) {
    throw new ApiError(
      response.status,
      body.error.code,
      body.error.message,
      body.error.details ?? null,
    );
  }
  throw networkError();
}

/** Błędy walidacji przypięte do pól formularza: {pole: komunikat}. */
export function fieldErrors(err: unknown): Record<string, string> {
  if (
    !(err instanceof ApiError) ||
    err.code !== "validation_error" ||
    !Array.isArray(err.details)
  ) {
    return {};
  }
  const out: Record<string, string> = {};
  for (const d of err.details as Array<{ field?: unknown; message?: unknown }>) {
    if (typeof d.field === "string" && typeof d.message === "string" && !(d.field in out)) {
      out[d.field] = d.message;
    }
  }
  return out;
}
