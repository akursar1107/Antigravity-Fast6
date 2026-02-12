import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import PlayerStatsTable from "../PlayerStatsTable";
import type { PlayerStat } from "@/lib/api";

describe("PlayerStatsTable", () => {
  const mockData: PlayerStat[] = [
    {
      player_name: "Tyreek Hill",
      team: "MIA",
      first_td_count: 6,
      any_time_td_rate: 0.75,
      accuracy: 62.5,
    },
    {
      player_name: "Christian McCaffrey",
      team: "SF",
      first_td_count: 5,
      any_time_td_rate: 0.80,
      accuracy: 55.0,
    },
    {
      player_name: "A.J. Brown",
      team: "PHI",
      first_td_count: 4,
      any_time_td_rate: 0.60,
      accuracy: 48.0,
    },
  ];

  it("renders table with data", () => {
    render(<PlayerStatsTable data={mockData} />);
    
    expect(screen.getByLabelText("Player performance statistics")).toBeInTheDocument();
    expect(screen.getByText("Tyreek Hill")).toBeInTheDocument();
    expect(screen.getByText("Christian McCaffrey")).toBeInTheDocument();
    expect(screen.getByText("A.J. Brown")).toBeInTheDocument();
  });

  it("renders empty state when no data", () => {
    render(<PlayerStatsTable data={[]} />);
    
    expect(screen.getByText("No data yet")).toBeInTheDocument();
    expect(screen.getByText("Player stats will populate once picks are graded")).toBeInTheDocument();
  });

  it("formats percentages to 0 decimal places", () => {
    render(<PlayerStatsTable data={mockData} />);
    
    // Check any-time TD rate formatting (75% from 0.75)
    expect(screen.getByText("75%")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument();
    expect(screen.getByText("60%")).toBeInTheDocument();
  });

  it("displays correct first TD counts", () => {
    render(<PlayerStatsTable data={mockData} />);
    
    const rows = screen.getAllByRole("row");
    // Header + 3 data rows
    expect(rows).toHaveLength(4);
    
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("applies correct color class for accuracy above 50%", () => {
    const { container } = render(<PlayerStatsTable data={mockData} />);
    
    // Find accuracy cells with success color (>= 50%)
    const successCells = container.querySelectorAll(".text-\\[\\#15803d\\]");
    expect(successCells.length).toBeGreaterThan(0);
  });

  it("handles 0% accuracy edge case", () => {
    const zeroAccuracyData: PlayerStat[] = [
      {
        player_name: "Test Player",
        team: "TB",
        first_td_count: 0,
        any_time_td_rate: 0,
        accuracy: 0,
      },
    ];
    const { container } = render(<PlayerStatsTable data={zeroAccuracyData} />);
    
    // Verify 0% accuracy is rendered with muted color (< 50%)
    const accuracyCell = container.querySelector("td:last-child .text-\\[\\#78716c\\]");
    expect(accuracyCell).toBeInTheDocument();
    expect(accuracyCell?.textContent).toBe("0%");
  });

  it("applies success color for exactly 50% accuracy boundary", () => {
    const boundaryData: PlayerStat[] = [
      {
        player_name: "Boundary Player",
        team: "LAC",
        first_td_count: 3,
        any_time_td_rate: 0.5,
        accuracy: 50.0,
      },
    ];
    const { container } = render(<PlayerStatsTable data={boundaryData} />);
    
    // 50% should get success color (>= 50)
    const successCells = container.querySelectorAll(".text-\\[\\#15803d\\]");
    expect(successCells.length).toBe(1);
  });

  it("applies success color to specific rows with >= 50% accuracy", () => {
    const { container } = render(<PlayerStatsTable data={mockData} />);
    
    const rows = screen.getAllByRole("row");
    const dataRows = Array.from(rows).slice(1); // Skip header
    
    // Tyreek Hill: 62.5% - should be success
    const tyreekRow = dataRows[0];
    expect(tyreekRow.querySelector(".text-\\[\\#15803d\\]")).toBeInTheDocument();
    
    // Christian McCaffrey: 55% - should be success
    const cmcRow = dataRows[1];
    expect(cmcRow.querySelector(".text-\\[\\#15803d\\]")).toBeInTheDocument();
    
    // A.J. Brown: 48% - should NOT be success
    const ajRow = dataRows[2];
    expect(ajRow.querySelector(".text-\\[\\#15803d\\]")).not.toBeInTheDocument();
    expect(ajRow.querySelector(".text-\\[\\#78716c\\]")).toBeInTheDocument();
  });
});
