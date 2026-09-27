import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectEditDialog } from "../../../features/projects/ProjectEditDialog";
import type { Project } from "../../../features/projects/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/projects/hooks",
  () => ({
    useUpdateProject: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

vi.mock(
  "../../../features/projects/ProjectForm",
  () => ({
    ProjectForm: ({
      onSubmit,
      onCancel,
    }: {
      onSubmit: (values: {
        name: string;
        slug: string;
        description: string;
      }) => void | Promise<void>;
      onCancel: () => void;
    }) => (
      <div>
        <button
          type="button"
          onClick={() =>
            void onSubmit({
              name: "Updated Project",
              slug: "updated-project",
              description: "Updated description",
            })
          }
        >
          Submit Form
        </button>

        <button type="button" onClick={onCancel}>
          Cancel Form
        </button>
      </div>
    ),
  }),
);

const project: Project = {
  id: "project-1",
  organization_id: "org-1",
  name: "AI Evaluation",
  slug: "ai-evaluation",
  description: "Evaluation platform project",
  is_active: true,
};

describe("ProjectEditDialog", () => {
  it("renders when open with a project", () => {
    render(
      <ProjectEditDialog
        open
        project={project}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Edit Project" }),
    ).toBeInTheDocument();
  });

  it("does not render the form when project is null", () => {
    render(
      <ProjectEditDialog
        open
        project={null}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Edit Project" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Submit Form" }),
    ).not.toBeInTheDocument();
  });

  it("updates the selected project", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({});

    render(
      <ProjectEditDialog
        open
        project={project}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Submit Form" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      projectId: "project-1",
      payload: {
        name: "Updated Project",
        slug: "updated-project",
        description: "Updated description",
      },
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the form is cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ProjectEditDialog
        open
        project={project}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel Form" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});