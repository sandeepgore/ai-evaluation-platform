import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { OrganizationDeleteDialog } from "../../../features/organizations/OrganizationDeleteDialog";
import type { Organization } from "../../../features/organizations/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/organizations/hooks",
  () => ({
    useOrganizations: () => ({
      data: [
        {
          id: "org-1",
          name: "Demo Organization",
          slug: "demo-organization",
          description: "Development organization",
          is_active: true,
        },
      ],
    }),
    useDeleteOrganization: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

const organization: Organization = {
  id: "org-1",
  name: "Demo Organization",
  slug: "demo-organization",
  description: "Development organization",
  is_active: true,
};

describe("OrganizationDeleteDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("renders the organization confirmation", () => {
    render(
      <OrganizationDeleteDialog
        open
        organization={organization}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Delete Organization",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        'Are you sure you want to delete "Demo Organization"? This action cannot be undone.',
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Delete" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Cancel" }),
    ).toBeInTheDocument();
  });

  it("deletes the organization and closes the dialog", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockResolvedValue(undefined);

    render(
      <OrganizationDeleteDialog
        open
        organization={organization}
        onClose={onClose}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Delete" }),
    );

    await vi.waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith("org-1");
      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});