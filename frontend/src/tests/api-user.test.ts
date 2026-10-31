import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@/libs/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

import { api } from "@/libs/api";
import { loginUser, registerUser, getUserJwt, logoutUser } from "../api/user";

const mockPost = vi.mocked(api.post);
const mockGet = vi.mocked(api.get);

describe("user API", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
  });

  it("loginUser posts to /api/auth/login", async () => {
    mockPost.mockResolvedValueOnce({ data: { token: "abc" } });

    const res = await loginUser({ email: "a@b.com", password: "secret" });

    expect(mockPost).toHaveBeenCalledWith("/api/auth/login", {
      email: "a@b.com",
      password: "secret",
    });
    expect(res).toEqual({ token: "abc" });
  });

  it("registerUser posts to /api/auth/register", async () => {
    mockPost.mockResolvedValueOnce({ data: { id: 1 } });

    const res = await registerUser({
      name: "John",
      email: "john@test.com",
      password: "password123",
      passwordConfirmation: "password123",
    });

    expect(mockPost).toHaveBeenCalledWith("/api/auth/register", {
      name: "John",
      email: "john@test.com",
      password: "password123",
      passwordConfirmation: "password123",
    });
    expect(res).toEqual({ id: 1 });
  });

  it("getUserJwt gets from /api/user/jwt", async () => {
    mockGet.mockResolvedValueOnce({ data: { user: { id: "1" } } });

    const res = await getUserJwt();

    expect(mockGet).toHaveBeenCalledWith("/api/user/jwt");
    expect(res).toEqual({ user: { id: "1" } });
  });

  it("logoutUser posts to /api/auth/logout", async () => {
    mockPost.mockResolvedValueOnce({ data: { ok: true } });

    const res = await logoutUser();

    expect(mockPost).toHaveBeenCalledWith("/api/auth/logout");
    expect(res).toEqual({ ok: true });
  });

  it("propagates login errors", async () => {
    mockPost.mockRejectedValueOnce(new Error("Invalid credentials"));

    await expect(
      loginUser({ email: "a@b.com", password: "wrong" })
    ).rejects.toThrow("Invalid credentials");
  });
});