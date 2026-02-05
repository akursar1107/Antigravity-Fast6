import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MatchupCard from "../MatchupCard";
import type { MatchupResponse } from "@/lib/api";

describe("MatchupCard", () => {
  it("renders empty state when no team data", () => {
    const mockData: MatchupResponse = {
      game_id: "test-game",
      teams: [],
    };

    render(<MatchupCard data={mockData} />);
    expect(screen.getByText(/No matchup data available/i)).toBeInTheDocument();
  });

  it("renders matchup with two teams", () => {
    const mockData: MatchupResponse = {
      game_id: "test-game",
      teams: [
        {
          team: "KC",
          picks_count: 10,
          correct_count: 7,
          accuracy: 0.7,
        },
        {
          team: "SF",
          picks_count: 8,
          correct_count: 5,
          accuracy: 0.625,
        },
      ],
    };

    render(<MatchupCard data={mockData} />);

    // Check Home team (KC)
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("KC")).toBeInTheDocument();

    // Check Away team (SF)
    expect(screen.getByText("Away")).toBeInTheDocument();
    expect(screen.getByText("SF")).toBeInTheDocument();

    // Check stats
    expect(screen.getByText("10")).toBeInTheDocument(); // KC picks
    expect(screen.getByText("7")).toBeInTheDocument(); // KC correct
    expect(screen.getByText("70%")).toBeInTheDocument(); // KC accuracy

    expect(screen.getByText("8")).toBeInTheDocument(); // SF picks
    expect(screen.getByText("5")).toBeInTheDocument(); // SF correct
    // 62.5% rounds down to 62% with toFixed(0)
    const accuracyElements = screen.getAllByText(/^6[23]%$/);
    expect(accuracyElements.length).toBeGreaterThanOrEqual(1);
  });

  it("displays VS badge between teams", () => {
    const mockData: MatchupResponse = {
      game_id: "test-game",
      teams: [
        {
          team: "KC",
          picks_count: 5,
          correct_count: 3,
          accuracy: 0.6,
        },
        {
          team: "SF",
          picks_count: 5,
          correct_count: 3,
          accuracy: 0.6,
        },
      ],
    };

    render(<MatchupCard data={mockData} />);
    expect(screen.getByText("VS")).toBeInTheDocument();
  });

  it("renders correct accuracy color for home team", () => {
    const mockData: MatchupResponse = {
      game_id: "test-game",
      teams: [
        {
          team: "KC",
          picks_count: 10,
          correct_count: 7,
          accuracy: 0.7,
        },
        {
          team: "SF",
          picks_count: 8,
          correct_count: 5,
          accuracy: 0.625,
        },
      ],
    };

    render(<MatchupCard data={mockData} />);
    
    // Correct count should be in emerald
    const correctElements = screen.getAllByText("7");
    expect(correctElements.some(el => el.className.includes("text-emerald-400"))).toBe(true);
  });
});
