import { render, screen } from "./test-utils";
import { describe, it, expect } from "vitest";
import FullLoader from "../components/FullLoader";

describe("FullLoader", () => {
  it("renders default loading text", () => {
    render(<FullLoader />);
    const loadingTexts = screen.getAllByText(/loading.../i);
    expect(loadingTexts.length).toBeGreaterThan(0);
    const statuses = screen.getAllByRole("status");
    expect(statuses.length).toBeGreaterThan(0);
  });

  it("renders custom text", () => {
    render(<FullLoader text="Processing evaluation..." />);
    expect(screen.getByText(/processing evaluation/i)).toBeInTheDocument();
  });

  it("has role status for accessibility", () => {
    render(<FullLoader />);
    const statuses = screen.getAllByRole("status");
    expect(statuses.length).toBeGreaterThan(0);
  });
});