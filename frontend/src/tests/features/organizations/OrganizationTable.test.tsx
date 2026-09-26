import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { Organization } from "../../../features/organizations/api";
import { OrganizationTable } from "../../../features/organizations/OrganizationTable";

const organization: Organization = {
  id: "org-1",
  name: "Demo Organization",
  slug: "demo-organization",
  description: "Development organization",
  is_active: true,
};

describe("OrganizationTable", () => {
  it("renders organization details", () => {
    render(
      <OrganizationTable
        organizations={[organization]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(
      screen.getByText("Demo Organization"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("demo-organization"),
    ).toBeInTheDocument();

    expect(
      screen.getByText("Development organization"),
    ).toBeInTheDocument();

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("calls edit when the edit action is clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <OrganizationTable
        organizations={[organization]}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Edit Demo Organization",
      }),
    );

    expect(onEdit).toHaveBeenCalledWith(organization);
  });

  it("calls delete when the delete action is clicked", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <OrganizationTable
        organizations={[organization]}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Delete Demo Organization",
      }),
    );

    expect(onDelete).toHaveBeenCalledWith(organization);
  });
});