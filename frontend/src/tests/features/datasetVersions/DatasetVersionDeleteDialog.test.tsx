import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionDeleteDialog } from "../../../features/datasetVersions/DatasetVersionDeleteDialog";
import type { DatasetVersion } from "../../../features/datasetVersions/api";
import { useDeleteDatasetVersion } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useDeleteDatasetVersion: vi.fn(),
}));

const mockedUseDeleteDatasetVersion = vi.mocked(useDeleteDatasetVersion);

const version: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 2,
  status: "draft",
  description: "Draft version",
  case_count: 0,
  is_active: true,
};

describe("DatasetVersionDeleteDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseDeleteDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(undefined),
      isPending: false,
    } as never);
  });

  it("renders the confirmation dialog", () => {
    render(
      <DatasetVersionDeleteDialog open version={version} onClose={vi.fn()} />,
    );

    expect(
      screen.getByRole("dialog", { name: "Delete Dataset Version" }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Are you sure you want to delete version 2? This action cannot be undone.",
      ),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetVersionDeleteDialog
        open={false}
        version={version}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", {
        name: "Delete Dataset Version",
      }),
    ).not.toBeInTheDocument();
  });

  it("renders an empty message when version is null", () => {
    render(
      <DatasetVersionDeleteDialog open version={null} onClose={vi.fn()} />,
    );

    expect(
      screen.getByRole("dialog", {
        name: "Delete Dataset Version",
      }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("deletes the selected version", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    mockedUseDeleteDatasetVersion.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionDeleteDialog open version={version} onClose={onClose} />,
    );

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith("version-1");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetVersionDeleteDialog open version={version} onClose={onClose} />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("disables actions while deleting", () => {
    mockedUseDeleteDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetVersionDeleteDialog open version={version} onClose={vi.fn()} />,
    );

    expect(
      screen.getByRole("button", { name: "Processing..." }),
    ).toBeDisabled();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });
});
