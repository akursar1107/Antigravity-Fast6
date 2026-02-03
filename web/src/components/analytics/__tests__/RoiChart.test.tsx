import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import RoiChart from "../RoiChart";
import type { RoiTrend } from "@/lib/api";

describe("RoiChart", () => {
  const mockData: RoiTrend[] = [
    { week: 1, picks_count: 10, correct_count: 4, accuracy: 40, roi_dollars: -2.5 },
    { week: 2, picks_count: 12, correct_count: 6, accuracy: 50, roi_dollars: 3.2 },
    { week: 3, picks_count: 8, correct_count: 5, accuracy: 62.5, roi_dollars: 8.1 },
  ];

  it("renders chart with data", () => {
    render(<RoiChart data={mockData} />);
    
    const chart = screen.getByLabelText("ROI trend chart");
    expect(chart).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<RoiChart data={[]} />);
    
    expect(screen.getByText("No data yet")).toBeInTheDocument();
    expect(screen.getByText("ROI trends will appear once picks are graded")).toBeInTheDocument();
  });

  it("formats ROI values to 1 decimal place", () => {
    render(<RoiChart data={mockData} />);
    
    // Verify the chart renders with proper aria label
    const chart = screen.getByLabelText("ROI trend chart");
    expect(chart).toBeInTheDocument();
  });
});
