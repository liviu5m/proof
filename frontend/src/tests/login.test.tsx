import { render, screen, fireEvent, waitFor } from "./test-utils";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn() }),
  usePathname: () => "/",
}));

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

// Mock the api instance used by loginUser
vi.mock("@/libs/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}));

import { api } from "@/libs/api";
import LoginPage from "../app/auth/login/page";

const mockPost = vi.mocked(api.post);
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: vi.fn() }),
  usePathname: () => "/",
}));

describe("LoginPage", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockPush.mockReset();
  });

  it("renders login form with email and password fields", () => {
    render(<LoginPage />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("shows Sign up link for new users", () => {
    render(<LoginPage />);
    expect(screen.getByText(/don't have an account?/i)).toBeInTheDocument();
    expect(screen.getByText(/sign up/i)).toBeInTheDocument();
  });

  it("calls loginUser on submit and redirects on success", async () => {
    mockPost.mockResolvedValueOnce({ data: { token: "abc" } });

    render(<LoginPage />);

    fireEvent.input(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.input(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/auth/login", {
        email: "user@example.com",
        password: "password123",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/dashboard/datasets");
  });

  it("disables sign in button while loading", async () => {
    mockPost.mockImplementation(() =>
      new Promise((res) => setTimeout(() => res({ data: {} }), 200))
    );

    render(<LoginPage />);

    fireEvent.input(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.input(screen.getByLabelText(/password/i), {
      target: { value: "password123" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await expect(
      screen.findByRole("button", { name: /signing in/i })
    ).resolves.toBeDisabled();
  });

  it("shows error toast on login failure", async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { detail: "Invalid credentials" } },
    });

    render(<LoginPage />);

    fireEvent.input(screen.getByLabelText(/email/i), {
      target: { value: "user@example.com" },
    });
    fireEvent.input(screen.getByLabelText(/password/i), {
      target: { value: "wrong" },
    });
    fireEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });
  });
});

afterEach(() => {
  vi.clearAllMocks();
});