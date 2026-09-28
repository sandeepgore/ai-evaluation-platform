import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetCreateDialog } from "../../../features/datasets/DatasetCreateDialog";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/datasets/hooks",
  () => ({
    useCreateDataset: () => ({
      mutateAsync,
      isPending: false,
    }),
  }),
);

vi.mock(
  "../../../features/datasets/DatasetForm",
  () => ({
    DatasetForm: ({
      onSubmit,
      onCancel,
    }: {
      onSubmit: (values: {
        name: string;
        slug: string;
        description: string;
        dataset_type:
          | "generation"
          | "classification"
          | "rag"
          | "conversation"
          | "custom";
      }) => void | Promise<void>;
      onCancel: () => void;
    }) => (
      <div>
        <button
          type="button"
          onClick={() =>
            void onSubmit({
              name: "New Dataset",
              slug: "new-dataset",
              description: "Description",
              dataset_type: "rag",
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

describe("DatasetCreateDialog", () => {
  it("renders when open", () => {
    render(
      <DatasetCreateDialog
        open
        projectId="project-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Create Dataset" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetCreateDialog
        open={false}
        projectId="project-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("heading", { name: "Create Dataset" }),
    ).not.toBeInTheDocument();
  });

  it("creates a dataset with the project id", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({});

    render(
      <DatasetCreateDialog
        open
        projectId="project-1"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Submit Form" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      project_id: "project-1",
      name: "New Dataset",
      slug: "new-dataset",
      description: "Description",
      dataset_type: "rag",
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the form is cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetCreateDialog
        open
        projectId="project-1"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel Form" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
