import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import WeekPicksTable from "../WeekPicksTable";
import type { WeekPick } from "@/lib/api";

describe("WeekPicksTable", () => {
  it("renders empty state when no picks", () => {
    render(<WeekPicksTable picks={[]} />);
    expect(screen.getByText(/No picks for this week yet/i)).toBeInTheDocument();
  });

  it("renders table with picks data", () => {
    const mockPicks: WeekPick[] = [
      {
        id: 1,
        user_id: 1,
        user_name: "John Doe",
        team: "KC",
        player_name: "Patrick Mahomes",
        odds: 250,
        graded: true,
        is_correct: true,
        actual_scorer: "Patrick Mahomes",
      },
      {
        id: 2,
        user_id: 2,
        user_name: "Jane Smith",
        team: "SF",
        player_name: "Christian McCaffrey",
        odds: -110,
        graded: false,
        is_correct: null,
        actual_scorer: null,
      },
    ];

    render(<WeekPicksTable picks={mockPicks} />);

    // Check table headers
    expect(screen.getByText("User")).toBeInTheDocument();
    expect(screen.getByText("Team")).toBeInTheDocument();
    expect(screen.getByText("Player")).toBeInTheDocument();
    expect(screen.getByText("Odds")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Result")).toBeInTheDocument();

    // Check data rows
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("KC")).toBeInTheDocument();
    // Check for players in table cells (avoid multiple text nodes)
    const patrickCells = screen.getAllByText("Patrick Mahomes");
    expect(patrickCells.length).toBeGreaterThan(0);
    expect(screen.getByText("+250")).toBeInTheDocument();

    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
    expect(screen.getByText("SF")).toBeInTheDocument();
    const christianCells = screen.getAllByText("Christian McCaffrey");
    expect(christianCells.length).toBeGreaterThan(0);
    expect(screen.getByText("-110")).toBeInTheDocument();
  });

  it("displays Correct status badge with success color", () => {
    const mockPicks: WeekPick[] = [
      {
        id: 1,
        user_id: 1,
        user_name: "John Doe",
        team: "KC",
        player_name: "Patrick Mahomes",
        odds: 250,
        graded: true,
        is_correct: true,
        actual_scorer: "Patrick Mahomes",
      },
    ];

    render(<WeekPicksTable picks={mockPicks} />);
    const badge = screen.getByText("Correct");
    expect(badge).toHaveClass("text-[#15803d]");
  });

  it("displays Incorrect status badge with danger color", () => {
    const mockPicks: WeekPick[] = [
      {
        id: 1,
        user_id: 1,
        user_name: "John Doe",
        team: "KC",
        player_name: "Patrick Mahomes",
        odds: 250,
        graded: true,
        is_correct: false,
        actual_scorer: "Travis Kelce",
      },
    ];

    render(<WeekPicksTable picks={mockPicks} />);
    const badge = screen.getByText("Incorrect");
    expect(badge).toHaveClass("text-[#8C302C]");
  });

  it("displays Pending status badge with muted color", () => {
    const mockPicks: WeekPick[] = [
      {
        id: 1,
        user_id: 1,
        user_name: "John Doe",
        team: "KC",
        player_name: "Patrick Mahomes",
        odds: 250,
        graded: false,
        is_correct: null,
        actual_scorer: null,
      },
    ];

    render(<WeekPicksTable picks={mockPicks} />);
    const badge = screen.getByText("Pending");
    expect(badge).toHaveClass("text-[#78716c]");
  });

  it("formats odds correctly with + for positive and plain for negative", () => {
    const mockPicks: WeekPick[] = [
      {
        id: 1,
        user_id: 1,
        user_name: "User 1",
        team: "KC",
        player_name: "Player 1",
        odds: 300,
        graded: false,
        is_correct: null,
        actual_scorer: null,
      },
      {
        id: 2,
        user_id: 2,
        user_name: "User 2",
        team: "SF",
        player_name: "Player 2",
        odds: -150,
        graded: false,
        is_correct: null,
        actual_scorer: null,
      },
    ];

    render(<WeekPicksTable picks={mockPicks} />);
    expect(screen.getByText("+300")).toBeInTheDocument();
    expect(screen.getByText("-150")).toBeInTheDocument();
  });
});
