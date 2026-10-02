import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetCaseDeleteDialog } from "../../../features/datasetCases/DatasetCaseDeleteDialog";
import type { DatasetCase } from "../../../features/datasetCases/api";
import { useDeleteDatasetCase } from "../../../features/datasetCases/hooks";

vi.mock("../../../features/datasetCases/hooks", () => ({
  useDeleteDatasetCase: vi.fn(),
}));

const mockedUseDeleteDatasetCase = vi.mocked(useDeleteDatasetCase);

const datasetCase: DatasetCase = {
  id: "case-1",
  dataset_version_id: "version-1",
  input: "Test input",
  expected_output: "Test output",
  case_metadata: null,
  has_reference: false,
  has_context: false,
  position: 0,
  is_active: true,
};

describe("DatasetCaseDeleteDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseDeleteDatasetCase.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
      isPending: false,
    } as never);
  });

  it("renders the confirmation dialog", () => {
    render(
      <DatasetCaseDeleteDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Delete Dataset Case" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Are you sure you want to delete this dataset case? This action cannot be undone.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetCaseDeleteDialog
        open={false}
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Delete Dataset Case" }),
    ).not.toBeInTheDocument();
  });

  it("renders an empty message when case is null", () => {
    render(
      <DatasetCaseDeleteDialog
        open
        datasetCase={null}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Delete Dataset Case" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("deletes the selected case", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    mockedUseDeleteDatasetCase.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetCaseDeleteDialog
        open
        datasetCase={datasetCase}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith("case-1");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetCaseDeleteDialog
        open
        datasetCase={datasetCase}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("disables actions while deleting", () => {
    mockedUseDeleteDatasetCase.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetCaseDeleteDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Processing..." }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
