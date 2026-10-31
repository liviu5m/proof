import { render, screen, fireEvent } from "./test-utils";
import { describe, it, expect } from "vitest";
import { Input } from "../components/ui/input";

describe("Input", () => {
  it("renders an input element", () => {
    render(<Input id="email" placeholder="Enter email" />);
    expect(screen.getByPlaceholderText("Enter email")).toBeInTheDocument();
  });

  it("is disabled when disabled prop is passed", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("captures user input via onChange", () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    const input = screen.getByRole("textbox");
    fireEvent.input(input, { target: { value: "test@example.com" } });
    expect(handleChange).toHaveBeenCalled();
  });
});

import { vi } from "vitest";