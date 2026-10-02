import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetCaseCreateDialog } from "../../../features/datasetCases/DatasetCaseCreateDialog";
import { useCreateDatasetCase } from "../../../features/datasetCases/hooks";

vi.mock("../../../features/datasetCases/hooks", () => ({
  useCreateDatasetCase: vi.fn(),
}));

const mockedUseCreateDatasetCase = vi.mocked(useCreateDatasetCase);

describe("DatasetCaseCreateDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseCreateDatasetCase.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({
        id: "case-1",
        dataset_version_id: "version-1",
        input: "Test input",
        expected_output: "Test output",
        case_metadata: null,
        has_reference: false,
        has_context: false,
        position: 0,
        is_active: true,
      }),
      isPending: false,
    } as never);
  });

  it("renders when open", () => {
    render(
      <DatasetCaseCreateDialog
        open
        datasetVersionId="version-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Add Dataset Case" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Input" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add Case" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetCaseCreateDialog
        open={false}
        datasetVersionId="version-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Add Dataset Case" }),
    ).not.toBeInTheDocument();
  });

  it("creates a case with the expected payload", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({});
    const onClose = vi.fn();

    mockedUseCreateDatasetCase.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetCaseCreateDialog
        open
        datasetVersionId="version-1"
        onClose={onClose}
      />,
    );

    await user.type(
      screen.getByRole("textbox", { name: "Input" }),
      "Test input",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Expected Output" }),
      "Test output",
    );
    const metadata = screen.getByRole("textbox", {
      name: "Metadata (JSON)",
    });

    await user.click(metadata);
    await user.paste('{"category":"rag"}');

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      dataset_version_id: "version-1",
      input: "Test input",
      expected_output: "Test output",
      case_metadata: {
        category: "rag",
      },
    });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("sends null for empty expected output and metadata", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({});

    mockedUseCreateDatasetCase.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetCaseCreateDialog
        open
        datasetVersionId="version-1"
        onClose={vi.fn()}
      />,
    );

    await user.type(
      screen.getByRole("textbox", { name: "Input" }),
      "Test input",
    );

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      dataset_version_id: "version-1",
      input: "Test input",
      expected_output: null,
      case_metadata: null,
    });
  });

  it("disables form actions while creating", () => {
    mockedUseCreateDatasetCase.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetCaseCreateDialog
        open
        datasetVersionId="version-1"
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Input" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
