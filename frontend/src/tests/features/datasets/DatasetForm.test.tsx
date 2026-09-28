import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetForm } from "../../../features/datasets/DatasetForm";
import type { Dataset } from "../../../features/datasets/api";

const dataset: Dataset = {
  id: "dataset-1",
  project_id: "project-1",
  name: "Evaluation Dataset",
  slug: "evaluation-dataset",
  description: "Evaluation dataset",
  dataset_type: "rag",
  is_active: true,
};

describe("DatasetForm", () => {
  it("renders create mode fields and actions", () => {
    render(<DatasetForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Name")).toHaveValue("");
    expect(screen.getByLabelText("Slug")).toHaveValue("");
    expect(screen.getByLabelText("Description")).toHaveValue("");
    expect(
      screen.getByRole("combobox", { name: "Dataset Type" }),
    ).toHaveTextContent("Custom");
    expect(
      screen.getByRole("button", { name: "Create Dataset" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("renders edit mode with dataset values", () => {
    render(
      <DatasetForm dataset={dataset} onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.getByLabelText("Name")).toHaveValue("Evaluation Dataset");
    expect(screen.getByLabelText("Slug")).toHaveValue("evaluation-dataset");
    expect(screen.getByLabelText("Description")).toHaveValue(
      "Evaluation dataset",
    );
    expect(
      screen.getByRole("combobox", { name: "Dataset Type" }),
    ).toHaveTextContent("RAG");
    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("submits valid form values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<DatasetForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText("Name"), "New Dataset");
    await user.type(screen.getByLabelText("Slug"), "new-dataset");
    await user.click(screen.getByRole("combobox", { name: "Dataset Type" }));

    await user.click(screen.getByRole("option", { name: "Classification" }));
    await user.type(
      screen.getByLabelText("Description"),
      "New dataset description",
    );

    await user.click(screen.getByRole("button", { name: "Create Dataset" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      {
        name: "New Dataset",
        slug: "new-dataset",
        description: "New dataset description",
        dataset_type: "classification",
      },
      expect.anything(),
    );
  });

  it("shows validation errors for required fields", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<DatasetForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Create Dataset" }));

    expect(screen.getByText("Name is required")).toBeInTheDocument();
    expect(screen.getByText("Slug is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onCancel", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(<DatasetForm onSubmit={vi.fn()} onCancel={onCancel} />);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables fields and shows Saving while submitting", () => {
    render(<DatasetForm submitting onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText("Name")).toBeDisabled();
    expect(screen.getByLabelText("Slug")).toBeDisabled();
    expect(
      screen.getByRole("combobox", { name: "Dataset Type" }),
    ).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByLabelText("Description")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
