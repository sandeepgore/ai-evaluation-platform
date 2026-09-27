import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectDeleteDialog } from "../../../features/projects/ProjectDeleteDialog";
import type { Project } from "../../../features/projects/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/projects/hooks",
  () => ({
    useDeleteProject: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

vi.mock(
  "../../../components/common/ConfirmDialog",
  () => ({
    ConfirmDialog: ({
      open,
      title,
      message,
      confirmLabel,
      onConfirm,
      onCancel,
    }: {
      open: boolean;
      title: string;
      message: string;
      confirmLabel: string;
      onConfirm: () => void;
      onCancel: () => void;
    }) =>
      open ? (
        <div role="dialog">
          <h2>{title}</h2>
          <p>{message}</p>
          <button type="button" onClick={onConfirm}>
            {confirmLabel}
          </button>
          <button type="button" onClick={onCancel}>
            Cancel
          </button>
        </div>
      ) : null,
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

describe("ProjectDeleteDialog", () => {
  it("renders the project confirmation message", () => {
    render(
      <ProjectDeleteDialog
        open
        project={project}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("Delete Project")).toBeInTheDocument();
    expect(
      screen.getByText(
        'Are you sure you want to delete "AI Evaluation"? This action cannot be undone.',
      ),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <ProjectDeleteDialog
        open={false}
        project={project}
        onClose={vi.fn()}
      />,
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("deletes the selected project", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);

    render(
      <ProjectDeleteDialog
        open
        project={project}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(mutateAsync).toHaveBeenCalledWith("project-1");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ProjectDeleteDialog
        open
        project={project}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});