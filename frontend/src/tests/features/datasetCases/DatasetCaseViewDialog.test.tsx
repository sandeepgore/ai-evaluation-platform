import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetCaseViewDialog } from "../../../features/datasetCases/DatasetCaseViewDialog";
import type { DatasetCase } from "../../../features/datasetCases/api";

const datasetCase: DatasetCase = {
  id: "case-1",
  dataset_version_id: "version-1",
  input: "What is RAG?",
  expected_output: "Retrieval augmented generation.",
  case_metadata: {
    category: "rag",
    source: "test",
  },
  has_reference: true,
  has_context: true,
  position: 0,
  is_active: true,
};

describe("DatasetCaseViewDialog", () => {
  it("renders the selected case", () => {
    render(
      <DatasetCaseViewDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Dataset Case" }),
    ).toBeInTheDocument();
    expect(screen.getByText("What is RAG?")).toBeInTheDocument();
    expect(
      screen.getByText("Retrieval augmented generation."),
    ).toBeInTheDocument();
    expect(screen.getByText("Metadata")).toBeInTheDocument();
    expect(screen.getByText(/"category": "rag"/)).toBeInTheDocument();
    expect(screen.getByText(/"source": "test"/)).toBeInTheDocument();
  });

  it("shows Not provided when expected output is missing", () => {
    render(
      <DatasetCaseViewDialog
        open
        datasetCase={{
          ...datasetCase,
          expected_output: null,
        }}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("Not provided")).toBeInTheDocument();
  });

  it("does not render metadata when metadata is null", () => {
    render(
      <DatasetCaseViewDialog
        open
        datasetCase={{
          ...datasetCase,
          case_metadata: null,
        }}
        onClose={vi.fn()}
      />,
    );

    expect(screen.queryByText("Metadata")).not.toBeInTheDocument();
  });

  it("does not render case content when case is null", () => {
    render(<DatasetCaseViewDialog open datasetCase={null} onClose={vi.fn()} />);

    expect(
      screen.getByRole("dialog", { name: "Dataset Case" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Input")).not.toBeInTheDocument();
  });

  it("calls onClose when Escape is pressed", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetCaseViewDialog
        open
        datasetCase={datasetCase}
        onClose={onClose}
      />,
    );

    await user.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
