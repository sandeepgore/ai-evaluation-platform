import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAppContextStore } from "../../store/appContextStore";
import { OrganizationContextInitializer } from "../../components/context/OrganizationContextInitializer";

const useOrganizations = vi.fn();
const useProjects = vi.fn();

vi.mock(
  "../../features/organizations/hooks",
  () => ({
    useOrganizations: () => useOrganizations(),
  }),
);

vi.mock(
  "../../features/projects/hooks",
  () => ({
    useProjects: (organizationId: string | null) =>
      useProjects(organizationId),
  }),
);

describe("OrganizationContextInitializer", () => {
  beforeEach(() => {
    useOrganizations.mockReset();
    useProjects.mockReset();

    useAppContextStore.setState({
      selectedOrganizationId: null,
      selectedProjectId: null,
    });
  });

  it("selects the first organization when none is selected", async () => {
    useOrganizations.mockReturnValue({
      data: [
        {
          id: "org-1",
          name: "Newest Organization",
          slug: "newest-organization",
          description: null,
          is_active: true,
        },
        {
          id: "org-2",
          name: "Older Organization",
          slug: "older-organization",
          description: null,
          is_active: true,
        },
      ],
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedOrganizationId,
      ).toBe("org-1");
    });
  });

  it("selects the latest project when an organization has projects and none is selected", async () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: [
        {
          id: "org-1",
          name: "Selected Organization",
          slug: "selected-organization",
          description: null,
          is_active: true,
        },
      ],
    });

    useProjects.mockReturnValue({
      data: [
        {
          id: "project-new",
          organization_id: "org-1",
          name: "Newest Project",
          slug: "newest-project",
          description: null,
          is_active: true,
        },
        {
          id: "project-old",
          organization_id: "org-1",
          name: "Older Project",
          slug: "older-project",
          description: null,
          is_active: true,
        },
      ],
    });

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedProjectId,
      ).toBe("project-new");
    });

    expect(useProjects).toHaveBeenCalledWith("org-1");
  });

  it("does not overwrite an existing organization selection", async () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-2",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: [
        {
          id: "org-1",
          name: "Newest Organization",
          slug: "newest-organization",
          description: null,
          is_active: true,
        },
        {
          id: "org-2",
          name: "Selected Organization",
          slug: "selected-organization",
          description: null,
          is_active: true,
        },
      ],
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedOrganizationId,
      ).toBe("org-2");
    });
  });

  it("does not overwrite an existing project selection", async () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: "project-selected",
    });

    useOrganizations.mockReturnValue({
      data: [
        {
          id: "org-1",
          name: "Selected Organization",
          slug: "selected-organization",
          description: null,
          is_active: true,
        },
      ],
    });

    useProjects.mockReturnValue({
      data: [
        {
          id: "project-new",
          organization_id: "org-1",
          name: "Newest Project",
          slug: "newest-project",
          description: null,
          is_active: true,
        },
        {
          id: "project-selected",
          organization_id: "org-1",
          name: "Selected Project",
          slug: "selected-project",
          description: null,
          is_active: true,
        },
      ],
    });

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedProjectId,
      ).toBe("project-selected");
    });
  });

  it("does not select a project when no projects are available", async () => {
    useAppContextStore.setState({
      selectedOrganizationId: "org-1",
      selectedProjectId: null,
    });

    useOrganizations.mockReturnValue({
      data: [
        {
          id: "org-1",
          name: "Selected Organization",
          slug: "selected-organization",
          description: null,
          is_active: true,
        },
      ],
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedProjectId,
      ).toBeNull();
    });
  });

  it("does not select an organization when none are available", () => {
    useOrganizations.mockReturnValue({
      data: [],
    });

    useProjects.mockReturnValue({
      data: [],
    });

    render(<OrganizationContextInitializer />);

    expect(
      useAppContextStore.getState().selectedOrganizationId,
    ).toBeNull();
    expect(
      useAppContextStore.getState().selectedProjectId,
    ).toBeNull();
  });
});
