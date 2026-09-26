import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { OrganizationListPage } from "../../../features/organizations/OrganizationListPage";
import type { Organization } from "../../../features/organizations/api";

const useOrganizations = vi.fn();

vi.mock(
  "../../../features/organizations/hooks",
  () => ({
    useOrganizations: () => useOrganizations(),
  }),
);

vi.mock(
  "../../../features/organizations/OrganizationCreateDialog",
  () => ({
    OrganizationCreateDialog: ({
      open,
    }: {
      open: boolean;
      onClose: () => void;
    }) => (open ? <div role="dialog">Create Organization Dialog</div> : null),
  }),
);

vi.mock(
  "../../../features/organizations/OrganizationEditDialog",
  () => ({
    OrganizationEditDialog: ({
      open,
      organization,
    }: {
      open: boolean;
      organization: Organization | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Edit Organization Dialog: {organization?.name}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/organizations/OrganizationDeleteDialog",
  () => ({
    OrganizationDeleteDialog: ({
      open,
      organization,
    }: {
      open: boolean;
      organization: Organization | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Delete Organization Dialog: {organization?.name}
        </div>
      ) : null,
  }),
);

const organizations: Organization[] = [
  {
    id: "org-1",
    name: "Demo Organization",
    slug: "demo-organization",
    description: "Development organization",
    is_active: true,
  },
];

describe("OrganizationListPage", () => {
  beforeEach(() => {
    useOrganizations.mockReset();
  });

  it("renders the loading state", () => {
    useOrganizations.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<OrganizationListPage />);

    expect(
      screen.getByText("Loading organizations..."),
    ).toBeInTheDocument();
  });

  it("renders the error state", () => {
    useOrganizations.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<OrganizationListPage />);

    expect(
      screen.getByText("Unable to load organizations."),
    ).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    useOrganizations.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<OrganizationListPage />);

    expect(screen.getByText("No organizations yet")).toBeInTheDocument();
    expect(
      screen.getByText("Create your first organization to get started."),
    ).toBeInTheDocument();
  });

  it("renders organizations", () => {
    useOrganizations.mockReturnValue({
      data: organizations,
      isLoading: false,
      isError: false,
    });

    render(<OrganizationListPage />);

    expect(screen.getByText("Demo Organization")).toBeInTheDocument();
    expect(screen.getByText("demo-organization")).toBeInTheDocument();
  });

  it("opens the create dialog", async () => {
    const user = userEvent.setup();

    useOrganizations.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<OrganizationListPage />);

    await user.click(
      screen.getByRole("button", { name: "Create Organization" }),
    );

    expect(
      screen.getByText("Create Organization Dialog"),
    ).toBeInTheDocument();
  });

  it("opens the edit dialog for the selected organization", async () => {
    const user = userEvent.setup();

    useOrganizations.mockReturnValue({
      data: organizations,
      isLoading: false,
      isError: false,
    });

    render(<OrganizationListPage />);

    await user.click(
      screen.getByRole("button", { name: "Edit Demo Organization" }),
    );

    expect(
      screen.getByText("Edit Organization Dialog: Demo Organization"),
    ).toBeInTheDocument();
  });

  it("opens the delete dialog for the selected organization", async () => {
    const user = userEvent.setup();

    useOrganizations.mockReturnValue({
      data: organizations,
      isLoading: false,
      isError: false,
    });

    render(<OrganizationListPage />);

    await user.click(
      screen.getByRole("button", { name: "Delete Demo Organization" }),
    );

    expect(
      screen.getByText("Delete Organization Dialog: Demo Organization"),
    ).toBeInTheDocument();
  });
});