import { describe, it, expect } from "vitest";
import { cn, formatDate } from "../libs/utils";

describe("cn", () => {
  it("merges multiple class names", () => {
    expect(cn("px-2", "py-1", "text-red")).toBe("px-2 py-1 text-red");
  });

  it("lets later Tailwind classes win over earlier conflicting ones", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
  });

  it("handles undefined / null inputs", () => {
    expect(cn("a", undefined, null, "b")).toBe("a b");
  });
});

describe("formatDate", () => {
  it("formats an ISO date string", () => {
    expect(formatDate("2026-01-15")).toContain("Jan 15, 2026");
  });
});