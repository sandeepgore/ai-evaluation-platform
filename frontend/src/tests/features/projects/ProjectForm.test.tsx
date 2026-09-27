import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectForm } from "../../../features/projects/ProjectForm";
import type { Project } from "../../../features/projects/api";

const project: Project = {
  id: "project-1",
  organization_id: "org-1",
  name: "AI Evaluation",
  slug: "ai-evaluation",
  description: "Evaluation platform project",
  is_active: true,
};

describe("ProjectForm", () => {
  it("renders create mode fields and actions", () => {
    render(
      <ProjectForm
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Name")).toHaveValue("");
    expect(screen.getByLabelText("Slug")).toHaveValue("");
    expect(screen.getByLabelText("Description")).toHaveValue("");
    expect(
      screen.getByRole("button", { name: "Create Project" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel" }),
    ).toBeInTheDocument();
  });

  it("renders edit mode with project values", () => {
    render(
      <ProjectForm
        project={project}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Name")).toHaveValue("AI Evaluation");
    expect(screen.getByLabelText("Slug")).toHaveValue("ai-evaluation");
    expect(screen.getByLabelText("Description")).toHaveValue(
      "Evaluation platform project",
    );
    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("submits valid form values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<ProjectForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText("Name"), "New Project");
    await user.type(screen.getByLabelText("Slug"), "new-project");
    await user.type(
      screen.getByLabelText("Description"),
      "New project description",
    );

    await user.click(screen.getByRole("button", { name: "Create Project" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      {
        name: "New Project",
        slug: "new-project",
        description: "New project description",
      },
      expect.anything(),
    );
  });

  it("shows validation errors for required fields", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <ProjectForm
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Create Project" }),
    );

    expect(screen.getByText("Name is required")).toBeInTheDocument();
    expect(screen.getByText("Slug is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onCancel", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(
      <ProjectForm
        onSubmit={vi.fn()}
        onCancel={onCancel}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables fields and shows Saving while submitting", () => {
    render(
      <ProjectForm
        submitting
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Name")).toBeDisabled();
    expect(screen.getByLabelText("Slug")).toBeDisabled();
    expect(screen.getByLabelText("Description")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});