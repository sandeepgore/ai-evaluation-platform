import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetTable } from "../../../features/datasets/DatasetTable";
import type { Dataset } from "../../../features/datasets/api";

const datasets: Dataset[] = [
  {
    id: "dataset-1",
    project_id: "project-1",
    name: "RAG Evaluation",
    slug: "rag-evaluation",
    description: "RAG evaluation dataset",
    dataset_type: "rag",
    is_active: true,
  },
  {
    id: "dataset-2",
    project_id: "project-1",
    name: "Archived Dataset",
    slug: "archived-dataset",
    description: null,
    dataset_type: "custom",
    is_active: false,
  },
];

describe("DatasetTable", () => {
  it("renders dataset information", () => {
    render(
      <DatasetTable
        datasets={datasets}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("RAG Evaluation")).toBeInTheDocument();
    expect(screen.getByText("rag-evaluation")).toBeInTheDocument();
    expect(
      screen.getByText("RAG evaluation dataset"),
    ).toBeInTheDocument();

    expect(screen.getByText("Archived Dataset")).toBeInTheDocument();
    expect(screen.getByText("archived-dataset")).toBeInTheDocument();
    expect(screen.getByText("No description")).toBeInTheDocument();
  });

  it("renders dataset types", () => {
    render(
      <DatasetTable
        datasets={datasets}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("rag")).toBeInTheDocument();
    expect(screen.getByText("custom")).toBeInTheDocument();
  });

  it("renders dataset status", () => {
    render(
      <DatasetTable
        datasets={datasets}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("calls onEdit with the selected dataset", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <DatasetTable
        datasets={datasets}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Edit RAG Evaluation" }),
    );

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(datasets[0]);
  });

  it("calls onDelete with the selected dataset", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <DatasetTable
        datasets={datasets}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Delete RAG Evaluation" }),
    );

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(datasets[0]);
  });
});
