import { render, screen } from "@testing-library/react";
import DashboardLayout from "../DashboardLayout";

test("renders nav and content area", () => {
  render(
    <DashboardLayout>
      <div>Content</div>
    </DashboardLayout>
  );
  expect(screen.getAllByText(/Fast6/i).length).toBeGreaterThan(0);
  expect(screen.getByText("Content")).toBeInTheDocument();
});
