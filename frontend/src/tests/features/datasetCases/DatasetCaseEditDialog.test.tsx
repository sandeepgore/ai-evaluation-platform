import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetCaseEditDialog } from "../../../features/datasetCases/DatasetCaseEditDialog";
import type { DatasetCase } from "../../../features/datasetCases/api";
import { useUpdateDatasetCase } from "../../../features/datasetCases/hooks";

vi.mock("../../../features/datasetCases/hooks", () => ({
  useUpdateDatasetCase: vi.fn(),
}));

const mockedUseUpdateDatasetCase = vi.mocked(useUpdateDatasetCase);

const datasetCase: DatasetCase = {
  id: "case-1",
  dataset_version_id: "version-1",
  input: "Existing input",
  expected_output: "Existing output",
  case_metadata: {
    category: "rag",
  },
  has_reference: true,
  has_context: true,
  position: 0,
  is_active: true,
};

describe("DatasetCaseEditDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseUpdateDatasetCase.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(datasetCase),
      isPending: false,
    } as never);
  });

  it("renders when open with the selected case", () => {
    render(
      <DatasetCaseEditDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Edit Dataset Case" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Input" })).toHaveValue(
      "Existing input",
    );
    expect(
      screen.getByRole("textbox", { name: "Expected Output" }),
    ).toHaveValue("Existing output");
    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetCaseEditDialog
        open={false}
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Edit Dataset Case" }),
    ).not.toBeInTheDocument();
  });

  it("does not render the form when case is null", () => {
    render(
      <DatasetCaseEditDialog
        open
        datasetCase={null}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Edit Dataset Case" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("textbox", { name: "Input" }),
    ).not.toBeInTheDocument();
  });

  it("updates the selected case with the expected payload", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(datasetCase);
    const onClose = vi.fn();

    mockedUseUpdateDatasetCase.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetCaseEditDialog
        open
        datasetCase={datasetCase}
        onClose={onClose}
      />,
    );

    const input = screen.getByRole("textbox", { name: "Input" });

    await user.clear(input);
    await user.type(input, "Updated input");

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      caseId: "case-1",
      payload: {
        input: "Updated input",
        expected_output: "Existing output",
        case_metadata: {
          category: "rag",
        },
      },
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("sends null for cleared expected output and metadata", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(datasetCase);

    mockedUseUpdateDatasetCase.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetCaseEditDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    await user.clear(
      screen.getByRole("textbox", { name: "Expected Output" }),
    );
    await user.clear(
      screen.getByRole("textbox", { name: "Metadata (JSON)" }),
    );

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      caseId: "case-1",
      payload: {
        input: "Existing input",
        expected_output: null,
        case_metadata: null,
      },
    });
  });

  it("disables editing while updating", () => {
    mockedUseUpdateDatasetCase.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetCaseEditDialog
        open
        datasetCase={datasetCase}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Input" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
