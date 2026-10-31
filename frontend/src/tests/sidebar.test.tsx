import { render, screen } from "./test-utils";
import { describe, it, expect, vi } from "vitest";
import React from "react";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard/runs",
}));

import { Sidebar } from "../components/layout/sidebar";

describe("Sidebar", () => {
  it("renders navigation links", () => {
    render(<Sidebar />);
    const allRunsText = screen.getAllByText(/^runs$/i);
    expect(allRunsText.length).toBeGreaterThan(0);
    expect(screen.getByText(/^datasets$/i)).toBeInTheDocument();
    expect(screen.getByText(/new evaluation/i)).toBeInTheDocument();
    expect(screen.getByText(/compare runs/i)).toBeInTheDocument();
  });

  it("renders Proof logo and brand", () => {
    render(<Sidebar />);
    expect(screen.getByText(/^proof$/i)).toBeInTheDocument();
  });

  it("has a collapse/expand toggle button", () => {
    render(<Sidebar />);
    expect(
      screen.getByRole("button", { name: /collapse sidebar/i })
    ).toBeInTheDocument();
  });

  it("highlights the active navigation item", () => {
    render(<Sidebar />);
    // Check that the active nav link has primary styling by looking at
    // the link element that contains "Runs" text
    const allLinks = screen.getAllByRole("link");
    const runsLink = allLinks.find((el) => el.textContent === "Runs");
    expect(runsLink).toBeDefined();
    if (runsLink) {
      expect(runsLink.className).toContain("bg-primary");
    }
  });
});