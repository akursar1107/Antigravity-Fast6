import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LeaderboardTable from "../LeaderboardTable";
import type { LeaderboardEntry } from "@/lib/api";

describe("LeaderboardTable", () => {
  it("renders empty state when no data", () => {
    render(<LeaderboardTable data={[]} />);
    expect(screen.getByText("No data yet")).toBeInTheDocument();
    expect(
      screen.getByText("Leaderboard will populate once picks are graded")
    ).toBeInTheDocument();
  });

  it("renders table with all columns when data exists", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "Alice",
        weeks_participated: 5,
        total_picks: 10,
        correct_picks: 7,
        total_points: 21,
        roi_dollars: 150.5,
        win_percentage: 70.0,
      },
      {
        rank: 2,
        user_id: 2,
        user_name: "Bob",
        weeks_participated: 4,
        total_picks: 8,
        correct_picks: 4,
        total_points: 12,
        roi_dollars: -25.3,
        win_percentage: 50.0,
      },
    ];

    render(<LeaderboardTable data={mockData} />);

    // Check column headers
    expect(screen.getByText("Rank")).toBeInTheDocument();
    expect(screen.getByText("User")).toBeInTheDocument();
    expect(screen.getByText("Points")).toBeInTheDocument();
    expect(screen.getByText("ROI")).toBeInTheDocument();
    expect(screen.getByText("Win %")).toBeInTheDocument();
    expect(screen.getByText("Recent Form")).toBeInTheDocument();

    // Check first row data
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("21")).toBeInTheDocument();
    expect(screen.getByText("$150.5")).toBeInTheDocument();
    expect(screen.getAllByText("70%")).toHaveLength(2); // Win % and Recent Form

    // Check second row data
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("$-25.3")).toBeInTheDocument();
    expect(screen.getAllByText("50%")).toHaveLength(2); // Win % and Recent Form

    // Check medals for top 3
    expect(screen.getByText("🥇")).toBeInTheDocument();
  });

  it("formats ROI with one decimal place", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "Charlie",
        weeks_participated: 3,
        total_picks: 6,
        correct_picks: 4,
        total_points: 12,
        roi_dollars: 123.456,
        win_percentage: 66.67,
      },
    ];

    render(<LeaderboardTable data={mockData} />);
    expect(screen.getByText("$123.5")).toBeInTheDocument();
  });

  it("formats win percentage with zero decimal places", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "Dave",
        weeks_participated: 2,
        total_picks: 4,
        correct_picks: 3,
        total_points: 9,
        roi_dollars: 50.0,
        win_percentage: 75.5,
      },
    ];

    render(<LeaderboardTable data={mockData} />);
    expect(screen.getAllByText("76%")).toHaveLength(2); // Win % and Recent Form
  });

  it("displays medals for top 3 ranks", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "First",
        weeks_participated: 1,
        total_picks: 2,
        correct_picks: 2,
        total_points: 6,
        roi_dollars: 100.0,
        win_percentage: 100.0,
      },
      {
        rank: 2,
        user_id: 2,
        user_name: "Second",
        weeks_participated: 1,
        total_picks: 2,
        correct_picks: 1,
        total_points: 3,
        roi_dollars: 50.0,
        win_percentage: 50.0,
      },
      {
        rank: 3,
        user_id: 3,
        user_name: "Third",
        weeks_participated: 1,
        total_picks: 2,
        correct_picks: 1,
        total_points: 3,
        roi_dollars: 25.0,
        win_percentage: 50.0,
      },
    ];

    render(<LeaderboardTable data={mockData} />);
    expect(screen.getByText("🥇")).toBeInTheDocument();
    expect(screen.getByText("🥈")).toBeInTheDocument();
    expect(screen.getByText("🥉")).toBeInTheDocument();
  });

  it("handles user with 0 picks correctly", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "NoPicks",
        weeks_participated: 0,
        total_picks: 0,
        correct_picks: 0,
        total_points: 0,
        roi_dollars: 0.0,
        win_percentage: 0.0,
      },
    ];

    render(<LeaderboardTable data={mockData} />);
    expect(screen.getByText("NoPicks")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getAllByText("0%")).toHaveLength(2); // Win % and Recent Form
  });

  it("applies text-red-400 color for negative ROI", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "Loser",
        weeks_participated: 2,
        total_picks: 4,
        correct_picks: 1,
        total_points: 3,
        roi_dollars: -45.8,
        win_percentage: 25.0,
      },
    ];

    const { container } = render(<LeaderboardTable data={mockData} />);
    const roiElement = screen.getByText("$-45.8");
    expect(roiElement).toHaveClass("text-red-400");
  });

  it("applies correct color classes for recent form based on threshold", () => {
    const mockData: LeaderboardEntry[] = [
      {
        rank: 1,
        user_id: 1,
        user_name: "HighPerformer",
        weeks_participated: 2,
        total_picks: 4,
        correct_picks: 3,
        total_points: 9,
        roi_dollars: 50.0,
        win_percentage: 75.0,
      },
      {
        rank: 2,
        user_id: 2,
        user_name: "LowPerformer",
        weeks_participated: 2,
        total_picks: 4,
        correct_picks: 1,
        total_points: 3,
        roi_dollars: -10.0,
        win_percentage: 25.0,
      },
    ];

    const { container } = render(<LeaderboardTable data={mockData} />);
    
    // Find all elements with recent form percentages
    const highFormElement = screen.getAllByText("75%")[1]; // Second occurrence is Recent Form
    const lowFormElement = screen.getAllByText("25%")[1]; // Second occurrence is Recent Form
    
    expect(highFormElement).toHaveClass("text-emerald-400");
    expect(lowFormElement).toHaveClass("text-slate-400");
  });
});
