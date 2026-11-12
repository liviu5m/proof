import { render, screen, fireEvent, waitFor } from "./test-utils";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

vi.mock("@/libs/api", () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: { request: { use: vi.fn() } },
  },
}));

import { api } from "@/libs/api";
import SignupPage from "../app/auth/signup/page";

const mockPost = vi.mocked(api.post);
const mockPush = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

describe("SignupPage", () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockPush.mockReset();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders signup form with name, email, password fields", () => {
    render(<SignupPage />);
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    // password and confirm password both match /password/i, so use getAllByLabelText
    const passwordFields = screen.getAllByLabelText(/password/i);
    expect(passwordFields.length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("renders sign in link for existing users", () => {
    render(<SignupPage />);
    expect(screen.getByText(/already have an account?/i)).toBeInTheDocument();
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  it("calls registerUser on submit and redirects on success", async () => {
    mockPost.mockResolvedValueOnce({ data: { message: "User registered" } });

    render(<SignupPage />);

    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInputs = screen.getAllByLabelText(/password/i);

    fireEvent.input(nameInput, { target: { value: "Test User" } });
    fireEvent.input(emailInput, { target: { value: "user@example.com" } });
    fireEvent.input(passwordInputs[0], { target: { value: "password123" } });
    fireEvent.input(passwordInputs[1], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith("/api/auth/register", {
        name: "Test User",
        email: "user@example.com",
        password: "password123",
        passwordConfirmation: "password123",
      });
    });

    expect(mockPush).toHaveBeenCalledWith("/auth/login");
  });

  it("disables create account button while loading", async () => {
    mockPost.mockImplementation(() =>
      new Promise((res) => setTimeout(() => res({ data: {} }), 200))
    );

    render(<SignupPage />);

    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInputs = screen.getAllByLabelText(/password/i);

    fireEvent.input(nameInput, { target: { value: "Test User" } });
    fireEvent.input(emailInput, { target: { value: "user@example.com" } });
    fireEvent.input(passwordInputs[0], { target: { value: "password123" } });
    fireEvent.input(passwordInputs[1], { target: { value: "password123" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await expect(
      screen.findByRole("button", { name: /creating account/i })
    ).resolves.toBeDisabled();
  });

  it("shows error toast on signup failure", async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { detail: "Email already registered" } },
    });

    render(<SignupPage />);

    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInputs = screen.getAllByLabelText(/password/i);

    fireEvent.input(nameInput, { target: { value: "Test User" } });
    fireEvent.input(emailInput, { target: { value: "user@example.com" } });
    fireEvent.input(passwordInputs[0], { target: { value: "password123" } });
    fireEvent.input(passwordInputs[1], { target: { value: "wrong" } });
    fireEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalled();
    });
  });
});
