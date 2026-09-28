import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetEditDialog } from "../../../features/datasets/DatasetEditDialog";
import type { Dataset } from "../../../features/datasets/api";

const mutateAsync = vi.fn();

vi.mock(
  "../../../features/datasets/hooks",
  () => ({
    useUpdateDataset: () => ({
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
              name: "Updated Dataset",
              slug: "updated-dataset",
              description: "Updated description",
              dataset_type: "classification",
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

const dataset: Dataset = {
  id: "dataset-1",
  project_id: "project-1",
  name: "RAG Evaluation",
  slug: "rag-evaluation",
  description: "RAG evaluation dataset",
  dataset_type: "rag",
  is_active: true,
};

describe("DatasetEditDialog", () => {
  it("renders when open with a dataset", () => {
    render(
      <DatasetEditDialog
        open
        dataset={dataset}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Edit Dataset" }),
    ).toBeInTheDocument();
  });

  it("does not render the form when dataset is null", () => {
    render(
      <DatasetEditDialog
        open
        dataset={null}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Edit Dataset" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Submit Form" }),
    ).not.toBeInTheDocument();
  });

  it("updates the selected dataset without changing its project", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({});

    render(
      <DatasetEditDialog
        open
        dataset={dataset}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Submit Form" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      datasetId: "dataset-1",
      payload: {
        name: "Updated Dataset",
        slug: "updated-dataset",
        description: "Updated description",
        dataset_type: "classification",
      },
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when the form is cancelled", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetEditDialog
        open
        dataset={dataset}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel Form" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
