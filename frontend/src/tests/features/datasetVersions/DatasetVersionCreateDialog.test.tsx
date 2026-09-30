import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { DatasetVersionCreateDialog } from "../../../features/datasetVersions/DatasetVersionCreateDialog";
import { useCreateDatasetVersion } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useCreateDatasetVersion: vi.fn(),
}));

const mockedUseCreateDatasetVersion = vi.mocked(useCreateDatasetVersion);

describe("DatasetVersionCreateDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseCreateDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({
        id: "version-1",
        dataset_id: "dataset-1",
        version: 1,
        status: "draft",
        description: "Test version",
        case_count: 0,
        is_active: true,
      }),
      isPending: false,
    } as never);
  });

  it("renders when open", () => {
    render(
      <DatasetVersionCreateDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Create Dataset Version" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("spinbutton", { name: "Version" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("textbox", { name: "Description" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Create Version" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetVersionCreateDialog
        open={false}
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Create Dataset Version" }),
    ).not.toBeInTheDocument();
  });

  it("creates a version with the expected payload", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    const mutateAsync = vi.fn().mockResolvedValue({
      id: "version-1",
      dataset_id: "dataset-1",
      version: 5,
      status: "draft",
      description: "New version",
      case_count: 0,
      is_active: true,
    });

    mockedUseCreateDatasetVersion.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionCreateDialog
        open
        datasetId="dataset-1"
        onClose={onClose}
      />,
    );

    await user.clear(screen.getByRole("spinbutton", { name: "Version" }));

    await user.type(screen.getByRole("spinbutton", { name: "Version" }), "5");

    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "New version",
    );

    await user.click(screen.getByRole("button", { name: "Create Version" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      dataset_id: "dataset-1",
      version: 5,
      description: "New version",
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("sends null description when description is empty", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      id: "version-1",
      dataset_id: "dataset-1",
      version: 1,
      status: "draft",
      description: null,
      case_count: 0,
      is_active: true,
    });

    mockedUseCreateDatasetVersion.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionCreateDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Create Version" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      dataset_id: "dataset-1",
      version: 1,
      description: null,
    });
  });

  it("disables closing and form actions while creating", () => {
    mockedUseCreateDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetVersionCreateDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByRole("spinbutton", { name: "Version" })).toBeDisabled();

    expect(screen.getByRole("textbox", { name: "Description" })).toBeDisabled();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
