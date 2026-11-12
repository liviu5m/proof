import { render, screen } from "./test-utils";
import { describe, it, expect } from "vitest";
import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableCaption,
  TableFooter,
} from "../components/ui/table";

describe("Table components", () => {
  it("renders table with caption and footer", () => {
    render(
      <Table>
        <TableCaption>Sales data</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead>Month</TableHead>
            <TableHead>Revenue</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>January</TableCell>
            <TableCell>$1000</TableCell>
          </TableRow>
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell>Total</TableCell>
            <TableCell>$1000</TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    );
    expect(screen.getByText("Sales data")).toBeInTheDocument();
    expect(screen.getByText("January")).toBeInTheDocument();
    expect(screen.getByText("Total")).toBeInTheDocument();
  });
});
