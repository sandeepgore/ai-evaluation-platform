import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { OrganizationCreateDialog } from "../../../features/organizations/OrganizationCreateDialog";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/organizations/hooks",
  () => ({
    useCreateOrganization: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

describe("OrganizationCreateDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
  });

  it("renders the create organization form", () => {
    render(
      <OrganizationCreateDialog
        open
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", {
        name: "Create Organization",
      }),
    ).toBeInTheDocument();

    expect(screen.getByRole("textbox", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Slug" })).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Description" }),
    ).toBeInTheDocument();
  });

  it("creates an organization and closes the dialog", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockResolvedValue({
      id: "org-1",
      name: "Demo Organization",
      slug: "demo-organization",
      description: "Development organization",
      is_active: true,
    });

    render(
      <OrganizationCreateDialog
        open
        onClose={onClose}
      />,
    );

    await user.type(
      screen.getByRole("textbox", { name: "Name" }),
      "Demo Organization",
    );

    await user.type(
      screen.getByRole("textbox", { name: "Slug" }),
      "demo-organization",
    );

    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "Development organization",
    );

    await user.click(
      screen.getByRole("button", {
        name: "Create Organization",
      }),
    );

    await vi.waitFor(() => {
      expect(mutateAsync).toHaveBeenCalledWith({
        name: "Demo Organization",
        slug: "demo-organization",
        description: "Development organization",
      });

      expect(onClose).toHaveBeenCalledTimes(1);
    });
  });
});