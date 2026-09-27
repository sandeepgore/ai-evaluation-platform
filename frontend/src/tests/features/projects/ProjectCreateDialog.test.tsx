import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectCreateDialog } from "../../../features/projects/ProjectCreateDialog";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/projects/hooks",
  () => ({
    useCreateProject: () => ({
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
              name: "New Project",
              slug: "new-project",
              description: "Description",
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

describe("ProjectCreateDialog", () => {
  it("renders when open", () => {
    render(
      <ProjectCreateDialog
        open
        organizationId="org-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Create Project" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <ProjectCreateDialog
        open={false}
        organizationId="org-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("heading", { name: "Create Project" }),
    ).not.toBeInTheDocument();
  });

  it("creates a project with the organization id", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({});

    render(
      <ProjectCreateDialog
        open
        organizationId="org-1"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Submit Form" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      organization_id: "org-1",
      name: "New Project",
      slug: "new-project",
      description: "Description",
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the form is cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ProjectCreateDialog
        open
        organizationId="org-1"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel Form" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});