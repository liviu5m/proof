import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Loader from "../components/Loader";

describe("Loader", () => {
  it("renders with default text", () => {
    render(<Loader />);
    // The sr-only <span> also says "Loading...", so scope the query to the <p>
    expect(screen.getByText("Loading...", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
  it("renders with custom text", () => {
    render(<Loader text="Working..." />);
    expect(screen.getByText(/working.../i, { selector: "p" })).toBeInTheDocument();
  });
});
