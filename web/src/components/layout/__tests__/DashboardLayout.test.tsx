import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import DashboardLayout from "../DashboardLayout";

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
}));

test("renders nav and content area", () => {
  render(
    <DashboardLayout>
      <div>Content</div>
    </DashboardLayout>
  );
  expect(screen.getAllByText(/Fast6/i).length).toBeGreaterThan(0);
  expect(screen.getByText("Content")).toBeInTheDocument();
});
