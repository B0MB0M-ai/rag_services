import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "../app/page";

describe("phase one landing page", () => {
  it("identifies the product and preliminary assessment boundary", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "AI Service & Repair Assistant" })).toBeInTheDocument();
    expect(screen.getByText(/must be confirmed by a qualified technician/i)).toBeInTheDocument();
  });
});
