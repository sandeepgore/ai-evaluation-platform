import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardPage } from "../../../features/dashboard/DashboardPage";
import { useAppContextStore } from "../../../store/appContextStore";

const useOrganizations = vi.fn();

vi.mock("../../../features/organizations/hooks", () => ({
  useOrganizations: () => useOrganizations(),
}));

const organizations = [
  {
    id: "org-1",
    name: "Organization One",
    slug: "organization-one",
    description: null,
    is_active: true,
  },
  {
    id: "org-2",
    name: "Organization Two",
    slug: "organization-two",
    description: null,
    is_active: true,
  },
];

describe("DashboardPage", () => {
  beforeEach(() => {
    useOrganizations.mockReset();

    useAppContextStore.setState({
      selectedOrganizationId: null,
      selectedProjectId: null,
    });
  });

  it("renders dashboard content", () => {
    useOrganizations.mockReturnValue({
      data: organizations,
    });

    render(<DashboardPage />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText("Overview of your AI evaluation workspace."),
    ).toBeInTheDocument();
    expect(screen.getByText("Organization Context")).toBeInTheDocument();
  });

  it("renders available organizations", async () => {
    useOrganizations.mockReturnValue({
      data: organizations,
    });

    render(<DashboardPage />);

    const select = screen.getByRole("combobox", {
      name: "Organization",
    });

    await userEvent.setup().click(select);

    expect(
      screen.getByRole("option", { name: "Organization One" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Organization Two" }),
    ).toBeInTheDocument();
  });

  it("reflects the selected organization", () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-2",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    render(<DashboardPage />);

    expect(
      screen.getByRole("combobox", { name: "Organization" }),
    ).toHaveTextContent("Organization Two");
  });

  it("changes the selected organization", async () => {
    const user = userEvent.setup();

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    render(<DashboardPage />);

    await user.click(screen.getByRole("combobox", { name: "Organization" }));

    await user.click(screen.getByRole("option", { name: "Organization Two" }));

    expect(useAppContextStore.getState().selectedOrganizationId).toBe("org-2");
  });

  it("disables the selector when there are no organizations", () => {
    useOrganizations.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    expect(
      screen.getByRole("combobox", { name: "Organization" }),
    ).toHaveAttribute("aria-disabled", "true");
  });
});
