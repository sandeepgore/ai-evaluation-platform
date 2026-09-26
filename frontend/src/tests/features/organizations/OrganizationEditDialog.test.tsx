import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { OrganizationEditDialog } from "../../../features/organizations/OrganizationEditDialog";
import type { Organization } from "../../../features/organizations/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/organizations/hooks",
  () => ({
    useUpdateOrganization: () => ({
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

describe("OrganizationEditDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("renders the existing organization values", () => {
    render(
      <OrganizationEditDialog
        open
        organization={organization}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Edit Organization",
      }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("textbox", { name: "Name" }),
    ).toHaveValue("Demo Organization");

    expect(
      screen.getByRole("textbox", { name: "Slug" }),
    ).toHaveValue("demo-organization");

    expect(
      screen.getByRole("textbox", { name: "Description" }),
    ).toHaveValue("Development organization");

    expect(screen.getByRole("switch")).toBeChecked();
  });

  it("updates an organization and closes the dialog", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockResolvedValue({
      ...organization,
      name: "Updated Organization",
      slug: "updated-organization",
      description: "Updated description",
      is_active: false,
    });

    render(
      <OrganizationEditDialog
        open
        organization={organization}
        onClose={onClose}
      />,
    );

    const nameInput = screen.getByRole("textbox", { name: "Name" });
    const slugInput = screen.getByRole("textbox", { name: "Slug" });
    const descriptionInput = screen.getByRole("textbox", {
      name: "Description",
    });

    await user.clear(nameInput);
    await user.type(nameInput, "Updated Organization");

    await user.clear(slugInput);
    await user.type(slugInput, "updated-organization");

    await user.clear(descriptionInput);
    await user.type(descriptionInput, "Updated description");

    await user.click(screen.getByRole("switch"));

    await user.click(
      screen.getByRole("button", {
        name: "Save Changes",
      }),
    );

    await vi.waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        organizationId: "org-1",
        payload: {
          name: "Updated Organization",
          slug: "updated-organization",
          description: "Updated description",
          is_active: false,
        },
      });

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});