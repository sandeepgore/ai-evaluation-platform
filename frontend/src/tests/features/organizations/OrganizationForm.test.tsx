import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { OrganizationForm } from "../../../features/organizations/OrganizationForm";

describe("OrganizationForm", () => {
  it("renders create form fields", () => {
    render(<OrganizationForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Slug" })).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Description" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Create Organization" }),
    ).toBeInTheDocument();
  });

  it("shows validation errors for required fields", async () => {
    const user = userEvent.setup();

    render(<OrganizationForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    await user.click(
      screen.getByRole("button", { name: "Create Organization" }),
    );

    expect(screen.getByText("Name is required")).toBeInTheDocument();
    expect(screen.getByText("Slug is required")).toBeInTheDocument();
  });

  it("submits valid create values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<OrganizationForm onSubmit={onSubmit} onCancel={vi.fn()} />);

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
      screen.getByRole("button", { name: "Create Organization" }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      {
        name: "Demo Organization",
        slug: "demo-organization",
        description: "Development organization",
      },
      expect.anything(),
    );
  });

  it("renders edit values without active control", () => {
    render(
      <OrganizationForm
        organization={{
          id: "org-1",
          name: "Existing Organization",
          slug: "existing-organization",
          description: "Existing description",
          is_active: false,
        }}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Name" })).toHaveValue(
      "Existing Organization",
    );
    expect(screen.getByRole("textbox", { name: "Slug" })).toHaveValue(
      "existing-organization",
    );
    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "Existing description",
    );

    expect(screen.queryByRole("switch")).not.toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });
});
