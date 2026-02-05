import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clearCache } from "../cache";
import { getLeaderboard, getRoiTrends, request } from "../api";

describe("api request", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.stubGlobal("fetch", vi.fn());
    clearCache();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    clearCache();
  });

  it("returns data on success", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ ok: true }), { status: 200 })
    );

    const result = await request<{ ok: boolean }>("/health");

    expect(result).toEqual({ ok: true, data: { ok: true } });
  });

  it("retries once on 5xx and returns normalized error", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(new Response("oops", { status: 500 }))
      .mockResolvedValueOnce(new Response("oops", { status: 502 }));

    const result = await request("/boom");

    expect(result).toEqual({
      ok: false,
      error: { message: "Request failed", status: 502 },
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("caches GETs for 60s by URL", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ count: 1 }), { status: 200 })
    );

    const first = await request<{ count: number }>("/cached");
    const second = await request<{ count: number }>("/cached");

    expect(first).toEqual({ ok: true, data: { count: 1 } });
    expect(second).toEqual({ ok: true, data: { count: 1 } });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("expires cache after 60s", async () => {
    const fetchMock = vi.mocked(fetch);
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ count: 1 }), { status: 200 })
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ count: 2 }), { status: 200 })
      );

    const first = await request<{ count: number }>("/cached-expire");
    vi.advanceTimersByTime(60_001);
    const second = await request<{ count: number }>("/cached-expire");

    expect(first).toEqual({ ok: true, data: { count: 1 } });
    expect(second).toEqual({ ok: true, data: { count: 2 } });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("typed helpers use request", async () => {
    const fetchMock = vi.mocked(fetch);
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://example.test";
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([]), { status: 200 })
    );

    const result = await getLeaderboard(2025);

    expect(result).toEqual({ ok: true, data: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://example.test/api/leaderboard/season/2025",
      expect.any(Object)
    );

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("analytics helpers build query params", async () => {
    const fetchMock = vi.mocked(fetch);
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://example.test";
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify([]), { status: 200 })
    );

    const result = await getRoiTrends(2025);

    expect(result).toEqual({ ok: true, data: [] });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://example.test/api/analytics/roi-trends?season=2025",
      expect.any(Object)
    );
  });
});
