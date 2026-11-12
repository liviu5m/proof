import { render, screen } from "./test-utils";
import { describe, it, expect } from "vitest";
import React from "react";
import { Badge } from "../components/ui/badge";

describe("Badge", () => {
  it("renders default badge", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default")).toBeInTheDocument();
  });

  it("renders variant badges", () => {
    render(
      <div>
        <Badge variant="success">Success</Badge>
        <Badge variant="warning">Warning</Badge>
        <Badge variant="info">Info</Badge>
        <Badge variant="destructive">Destructive</Badge>
        <Badge variant="outline">Outline</Badge>
        <Badge variant="secondary">Secondary</Badge>
      </div>
    );
    expect(screen.getByText("Success")).toBeInTheDocument();
    expect(screen.getByText("Warning")).toBeInTheDocument();
    expect(screen.getByText("Info")).toBeInTheDocument();
    expect(screen.getByText("Destructive")).toBeInTheDocument();
    expect(screen.getByText("Outline")).toBeInTheDocument();
    expect(screen.getByText("Secondary")).toBeInTheDocument();
  });
});
