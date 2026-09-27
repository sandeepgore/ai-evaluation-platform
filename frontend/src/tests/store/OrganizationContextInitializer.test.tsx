import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useAppContextStore } from "../../store/appContextStore";
import { OrganizationContextInitializer } from "../../components/context/OrganizationContextInitializer";

const useOrganizations = vi.fn();

vi.mock(
  "../../features/organizations/hooks",
  () => ({
    useOrganizations: () => useOrganizations(),
  }),
);

describe("OrganizationContextInitializer", () => {
  beforeEach(() => {
    useOrganizations.mockReset();

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

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedOrganizationId,
      ).toBe("org-1");
    });
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

    render(<OrganizationContextInitializer />);

    await waitFor(() => {
      expect(
        useAppContextStore.getState().selectedOrganizationId,
      ).toBe("org-2");
    });
  });

  it("does not select an organization when none are available", () => {
    useOrganizations.mockReturnValue({
      data: [],
    });

    render(<OrganizationContextInitializer />);

    expect(
      useAppContextStore.getState().selectedOrganizationId,
    ).toBeNull();
  });
});