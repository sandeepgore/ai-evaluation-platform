import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionEditDialog } from "../../../features/datasetVersions/DatasetVersionEditDialog";
import type { DatasetVersion } from "../../../features/datasetVersions/api";
import { useUpdateDatasetVersion } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useUpdateDatasetVersion: vi.fn(),
}));

const mockedUseUpdateDatasetVersion = vi.mocked(useUpdateDatasetVersion);

const version: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 3,
  status: "draft",
  description: "Existing description",
  case_count: 0,
  is_active: true,
};

describe("DatasetVersionEditDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseUpdateDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue(version),
      isPending: false,
    } as never);
  });

  it("renders when open with the selected version", () => {
    render(
      <DatasetVersionEditDialog open version={version} onClose={vi.fn()} />,
    );

    expect(
      screen.getByRole("dialog", { name: "Edit Dataset Version" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "Existing description",
    );

    expect(
      screen.queryByRole("spinbutton", { name: "Version" }),
    ).not.toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <DatasetVersionEditDialog
        open={false}
        version={version}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Edit Dataset Version" }),
    ).not.toBeInTheDocument();
  });

  it("does not render the form when version is null", () => {
    render(<DatasetVersionEditDialog open version={null} onClose={vi.fn()} />);

    expect(
      screen.getByRole("dialog", { name: "Edit Dataset Version" }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("textbox", { name: "Description" }),
    ).not.toBeInTheDocument();
  });

  it("updates only the description", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      ...version,
      description: "Updated description",
    });
    const onClose = vi.fn();

    mockedUseUpdateDatasetVersion.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionEditDialog open version={version} onClose={onClose} />,
    );

    const description = screen.getByRole("textbox", {
      name: "Description",
    });

    await user.clear(description);
    await user.type(description, "Updated description");

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      versionId: "version-1",
      payload: {
        description: "Updated description",
      },
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("sends null when the description is cleared", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      ...version,
      description: null,
    });

    mockedUseUpdateDatasetVersion.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionEditDialog open version={version} onClose={vi.fn()} />,
    );

    await user.clear(screen.getByRole("textbox", { name: "Description" }));

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      versionId: "version-1",
      payload: {
        description: null,
      },
    });
  });

  it("disables editing while updating", () => {
    mockedUseUpdateDatasetVersion.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetVersionEditDialog open version={version} onClose={vi.fn()} />,
    );

    expect(screen.getByRole("textbox", { name: "Description" })).toBeDisabled();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
