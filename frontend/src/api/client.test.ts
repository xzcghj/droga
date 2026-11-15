import { afterEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, fieldErrors } from "./client";
import { formatMinutes } from "../lib/format";

function mockFetch(impl: () => Promise<Response>) {
  vi.stubGlobal("fetch", vi.fn(impl));
}

afterEach(() => vi.unstubAllGlobals());

describe("api client", () => {
  it("parses backend error format into ApiError", async () => {
    mockFetch(async () =>
      Response.json(
        {
          error: {
            code: "meetup_not_found",
            message: "Spotkanie o id 7 nie istnieje.",
            details: null,
          },
        },
        { status: 404 },
      ),
    );
    const err = await api("/meetups/7").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({
      status: 404,
      code: "meetup_not_found",
      message: "Spotkanie o id 7 nie istnieje.",
    });
  });

  it("maps network failure to network_error", async () => {
    mockFetch(async () => {
      throw new TypeError("Failed to fetch");
    });
    const err = await api("/meetups").catch((e: unknown) => e);
    expect(err).toMatchObject({
      status: 0,
      code: "network_error",
      message: "Brak połączenia z serwerem.",
    });
  });

  it("maps non-standard error body to network_error", async () => {
    mockFetch(async () => new Response("<html>502</html>", { status: 502 }));
    const err = await api("/meetups").catch((e: unknown) => e);
    expect(err).toMatchObject({ status: 0, code: "network_error" });
  });

  it("returns undefined for 204", async () => {
    mockFetch(async () => new Response(null, { status: 204 }));
    await expect(api("/meetups/1", { method: "DELETE" })).resolves.toBeUndefined();
  });

  it("sends json body with content type", async () => {
    const fetchMock = vi.fn(async () => Response.json({ id: 1 }, { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(api("/meetups", { method: "POST", json: { title: "Łódź" } })).resolves.toEqual({
      id: 1,
    });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/meetups");
    expect(init.body).toBe(JSON.stringify({ title: "Łódź" }));
    expect(new Headers(init.headers).get("Content-Type")).toBe("application/json");
  });

  it("fieldErrors maps validation details", () => {
    const err = new ApiError(422, "validation_error", "Niepoprawne dane", [
      { field: "title", message: "za długie" },
    ]);
    expect(fieldErrors(err)).toEqual({ title: "za długie" });
    expect(fieldErrors(new ApiError(404, "x", "y", null))).toEqual({});
  });
});

describe("format", () => {
  it("formatMinutes formats hours", () => {
    expect(formatMinutes(65)).toBe("1 h 05 min");
    expect(formatMinutes(18)).toBe("18 min");
    expect(formatMinutes(120)).toBe("2 h 00 min");
  });
});
