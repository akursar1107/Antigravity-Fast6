import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import DashboardLayout from "../DashboardLayout";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

vi.mock("@/components/analytics/RoiTrendsChartMulti", () => ({
  default: () => React.createElement("div", { "data-testid": "roi-chart" }, "ROI Chart"),
}));

test("renders nav and content area", () => {
  render(
    <DashboardLayout>
      <div>Content</div>
    </DashboardLayout>
  );
  expect(screen.getByText("Content")).toBeInTheDocument();
  // Nav labels visible (Board appears in sidebar and mobile nav)
  expect(screen.getAllByText("Board").length).toBeGreaterThan(0);
});
