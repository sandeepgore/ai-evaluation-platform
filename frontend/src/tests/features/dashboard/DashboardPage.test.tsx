import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardPage } from "../../../features/dashboard/DashboardPage";
import { useAppContextStore } from "../../../store/appContextStore";

const useOrganizations = vi.fn();
const useProjects = vi.fn();

vi.mock("../../../features/organizations/hooks", () => ({
  useOrganizations: () => useOrganizations(),
}));

vi.mock("../../../features/projects/hooks", () => ({
  useProjects: (organizationId: string | null) => useProjects(organizationId),
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

const projects = [
  {
    id: "project-1",
    organization_id: "org-1",
    name: "Project One",
    slug: "project-one",
    description: null,
    is_active: true,
  },
  {
    id: "project-2",
    organization_id: "org-1",
    name: "Project Two",
    slug: "project-two",
    description: null,
    is_active: true,
  },
];

describe("DashboardPage", () => {
  beforeEach(() => {
    useOrganizations.mockReset();
    useProjects.mockReset();

    useAppContextStore.setState({
      selectedOrganizationId: null,
      selectedProjectId: null,
    });
  });

  it("renders dashboard content", () => {
    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(
      screen.getByText("Overview of your AI evaluation workspace."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Organization" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("combobox", { name: "Project" }),
    ).toBeInTheDocument();
  });

  it("renders available organizations", async () => {
    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: [],
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

    useProjects.mockReturnValue({
      data: [],
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

    useProjects.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    await user.click(screen.getByRole("combobox", { name: "Organization" }));

    await user.click(screen.getByRole("option", { name: "Organization Two" }));

    expect(useAppContextStore.getState().selectedOrganizationId).toBe("org-2");
  });

  it("disables the organization selector when there are no organizations", () => {
    useOrganizations.mockReturnValue({
      data: [],
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    expect(
      screen.getByRole("combobox", { name: "Organization" }),
    ).toHaveAttribute("aria-disabled", "true");
  });

  it("renders available projects for the selected organization", async () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: projects,
    });

    render(<DashboardPage />);

    const select = screen.getByRole("combobox", {
      name: "Project",
    });

    await userEvent.setup().click(select);

    expect(
      screen.getByRole("option", { name: "Project One" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Project Two" }),
    ).toBeInTheDocument();

    expect(useProjects).toHaveBeenCalledWith("org-1");
  });

  it("reflects the selected project", () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: "project-2",
    });

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: projects,
    });

    render(<DashboardPage />);

    expect(screen.getByRole("combobox", { name: "Project" })).toHaveTextContent(
      "Project Two",
    );
  });

  it("changes the selected project", async () => {
    const user = userEvent.setup();

    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: "project-1",
    });

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: projects,
    });

    render(<DashboardPage />);

    await user.click(screen.getByRole("combobox", { name: "Project" }));

    await user.click(screen.getByRole("option", { name: "Project Two" }));

    expect(useAppContextStore.getState().selectedProjectId).toBe("project-2");
  });

  it("disables the project selector when no organization is selected", () => {
    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    expect(screen.getByRole("combobox", { name: "Project" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });

  it("disables the project selector when there are no projects", () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: organizations,
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<DashboardPage />);

    expect(screen.getByRole("combobox", { name: "Project" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });
});
