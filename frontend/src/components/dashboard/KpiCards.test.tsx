import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { KpiCards } from "./KpiCards";
import { Kpi } from "@/lib/types";

const kpis: Kpi[] = [
  { label: "Rows", value: 120, icon: "rows" },
  { label: "Quality Score", value: 87, suffix: "/100", icon: "quality" },
];

describe("KpiCards", () => {
  it("renders each KPI label and value", () => {
    render(<KpiCards kpis={kpis} />);
    expect(screen.getByText("Rows")).toBeInTheDocument();
    expect(screen.getByText("120")).toBeInTheDocument();
    expect(screen.getByText("Quality Score")).toBeInTheDocument();
    expect(screen.getByText("87")).toBeInTheDocument();
    expect(screen.getByText("/100")).toBeInTheDocument();
  });

  it("renders one card per KPI", () => {
    const { container } = render(<KpiCards kpis={kpis} />);
    expect(container.querySelectorAll(".card")).toHaveLength(kpis.length);
  });
});
