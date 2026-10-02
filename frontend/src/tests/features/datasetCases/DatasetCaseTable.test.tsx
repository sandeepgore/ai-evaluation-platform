import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetCaseTable } from "../../../features/datasetCases/DatasetCaseTable";
import type { DatasetCase } from "../../../features/datasetCases/api";

const datasetCases: DatasetCase[] = [
  {
    id: "case-1",
    dataset_version_id: "version-1",
    input: "What is retrieval augmented generation?",
    expected_output: "RAG combines retrieval with generation.",
    case_metadata: null,
    has_reference: true,
    has_context: true,
    position: 0,
    is_active: true,
  },
  {
    id: "case-2",
    dataset_version_id: "version-1",
    input: "Explain embeddings.",
    expected_output: null,
    case_metadata: null,
    has_reference: false,
    has_context: false,
    position: 1,
    is_active: true,
  },
];

const defaultProps = {
  cases: datasetCases,
  editable: true,
  ready: true,
  sortField: "position" as const,
  sortDirection: "asc" as const,
  onSort: vi.fn(),
  onView: vi.fn(),
  onEdit: vi.fn(),
  onDelete: vi.fn(),
};

describe("DatasetCaseTable", () => {
  it("renders dataset case information", () => {
    render(<DatasetCaseTable {...defaultProps} />);

    expect(
      screen.getByText("What is retrieval augmented generation?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("RAG combines retrieval with generation."),
    ).toBeInTheDocument();
    expect(screen.getByText("Explain embeddings.")).toBeInTheDocument();
    expect(screen.getByText("Not provided")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("hides reference and context columns when not ready", () => {
    render(<DatasetCaseTable {...defaultProps} ready={false} />);

    expect(screen.queryByText("Reference")).not.toBeInTheDocument();
    expect(screen.queryByText("Context")).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Reference available"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Context available"),
    ).not.toBeInTheDocument();
  });

  it("shows reference and context availability when ready", () => {
    render(<DatasetCaseTable {...defaultProps} />);

    expect(screen.getByText("Reference")).toBeInTheDocument();
    expect(screen.getByText("Context")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Reference available"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Reference not available"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Context available"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Context not available"),
    ).toBeInTheDocument();
  });

  it("calls onView with the selected case", async () => {
    const user = userEvent.setup();
    const onView = vi.fn();

    render(<DatasetCaseTable {...defaultProps} onView={onView} />);

    await user.click(
      screen.getByRole("button", { name: "View case 1" }),
    );

    expect(onView).toHaveBeenCalledTimes(1);
    expect(onView).toHaveBeenCalledWith(datasetCases[0]);
  });

  it("shows edit and delete actions only when editable", () => {
    const { rerender } = render(
      <DatasetCaseTable {...defaultProps} editable />,
    );

    expect(
      screen.getByRole("button", { name: "Edit case 1" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Delete case 1" }),
    ).toBeInTheDocument();

    rerender(
      <DatasetCaseTable {...defaultProps} editable={false} />,
    );

    expect(
      screen.queryByRole("button", { name: "Edit case 1" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Delete case 1" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "View case 1" }),
    ).toBeInTheDocument();
  });

  it("calls onEdit with the selected case", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(<DatasetCaseTable {...defaultProps} onEdit={onEdit} />);

    await user.click(
      screen.getByRole("button", { name: "Edit case 1" }),
    );

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(datasetCases[0]);
  });

  it("calls onDelete with the selected case", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(<DatasetCaseTable {...defaultProps} onDelete={onDelete} />);

    await user.click(
      screen.getByRole("button", { name: "Delete case 1" }),
    );

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(datasetCases[0]);
  });

  it("calls onSort when a sortable column is clicked", async () => {
    const user = userEvent.setup();
    const onSort = vi.fn();

    render(<DatasetCaseTable {...defaultProps} onSort={onSort} />);

    await user.click(screen.getByRole("button", { name: "Input" }));

    expect(onSort).toHaveBeenCalledTimes(1);
    expect(onSort).toHaveBeenCalledWith("input");
  });
});
