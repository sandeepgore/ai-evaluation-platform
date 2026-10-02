import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionListPage } from "../../../features/datasetVersions/DatasetVersionListPage";
import type { DatasetVersion } from "../../../features/datasetVersions/api";
import { useDataset } from "../../../features/datasets/hooks";

const useDatasetVersions = vi.fn();

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useDatasetVersions: (datasetId: string | null) =>
    useDatasetVersions(datasetId),
}));

vi.mock("../../../features/datasets/hooks", () => ({
  useDataset: vi.fn(),
}));

const mockedUseDataset = vi.mocked(useDataset);

vi.mock("../../../features/datasetVersions/DatasetVersionCreateDialog", () => ({
  DatasetVersionCreateDialog: ({
    open,
    datasetId,
  }: {
    open: boolean;
    datasetId: string;
    onClose: () => void;
  }) =>
    open ? <div role="dialog">Create Version Dialog: {datasetId}</div> : null,
}));

vi.mock("../../../features/datasetVersions/DatasetVersionImportDialog", () => ({
  DatasetVersionImportDialog: ({
    open,
    datasetId,
  }: {
    open: boolean;
    datasetId: string;
    onClose: () => void;
  }) =>
    open ? <div role="dialog">Import Version Dialog: {datasetId}</div> : null,
}));

vi.mock("../../../features/datasetVersions/DatasetVersionEditDialog", () => ({
  DatasetVersionEditDialog: ({
    open,
    version,
  }: {
    open: boolean;
    version: DatasetVersion | null;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog">Edit Version Dialog: v{version?.version}</div>
    ) : null,
}));

vi.mock("../../../features/datasetVersions/DatasetVersionDeleteDialog", () => ({
  DatasetVersionDeleteDialog: ({
    open,
    version,
  }: {
    open: boolean;
    version: DatasetVersion | null;
    onClose: () => void;
  }) =>
    open ? (
      <div role="dialog">Delete Version Dialog: v{version?.version}</div>
    ) : null,
}));

vi.mock(
  "../../../features/datasetVersions/DatasetVersionFinalizeDialog",
  () => ({
    DatasetVersionFinalizeDialog: ({
      open,
      version,
    }: {
      open: boolean;
      version: DatasetVersion | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">Finalize Version Dialog: v{version?.version}</div>
      ) : null,
  }),
);

const versions: DatasetVersion[] = [
  {
    id: "version-1",
    dataset_id: "dataset-1",
    version: 2,
    status: "ready",
    description: "Production version",
    case_count: 0,
    analytics: null,
    is_active: true,
  },
  {
    id: "version-2",
    dataset_id: "dataset-1",
    version: 1,
    status: "draft",
    description: null,
    case_count: 1,
    analytics: null,
    is_active: true,
  },
];

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/datasets/dataset-1/versions"]}>
      <Routes>
        <Route
          path="/datasets/:datasetId/versions"
          element={<DatasetVersionListPage />}
        />
        <Route
          path="/datasets/:datasetId/versions/:versionId"
          element={<div>Version Detail Page</div>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("DatasetVersionListPage", () => {
  beforeEach(() => {
    useDatasetVersions.mockReset();

    mockedUseDataset.mockReturnValue({
      data: {
        id: "dataset-1",
        name: "RAG Evaluation",
      },
      isLoading: false,
      isError: false,
    } as never);
  });

  it("renders the missing dataset ID state", () => {
    useDatasetVersions.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    render(
      <MemoryRouter>
        <DatasetVersionListPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Dataset ID is missing.")).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    useDatasetVersions.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    renderPage();

    expect(screen.getByText("Loading dataset versions...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    useDatasetVersions.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    renderPage();

    expect(
      screen.getByText("Unable to load dataset versions."),
    ).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    useDatasetVersions.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderPage();

    expect(screen.getByText("No versions yet")).toBeInTheDocument();

    expect(
      screen.getByText("Create or import a dataset version to get started."),
    ).toBeInTheDocument();
  });

  it("renders dataset versions", () => {
    useDatasetVersions.mockReturnValue({
      data: versions,
      isLoading: false,
      isError: false,
    });

    renderPage();

    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(screen.getByText("v1")).toBeInTheDocument();
    expect(screen.getByText("Production version")).toBeInTheDocument();
  });

  it("opens the create version dialog", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: "Create Version" }));

    expect(
      screen.getByText("Create Version Dialog: dataset-1"),
    ).toBeInTheDocument();
  });

  it("opens the import JSON dialog", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: "Import JSON" }));

    expect(
      screen.getByText("Import Version Dialog: dataset-1"),
    ).toBeInTheDocument();
  });

  it("opens the edit dialog for the selected version", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: versions,
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: "Edit version 2" }));

    expect(screen.getByText("Edit Version Dialog: v2")).toBeInTheDocument();
  });

  it("opens the delete dialog for the selected version", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: versions,
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: "Delete version 2" }));

    expect(screen.getByText("Delete Version Dialog: v2")).toBeInTheDocument();
  });

  it("opens the finalize dialog for the selected draft version", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: versions,
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(
      screen.getByRole("button", { name: "Finalize version 1" }),
    );

    expect(screen.getByText("Finalize Version Dialog: v1")).toBeInTheDocument();
  });

  it("navigates to the selected version detail page", async () => {
    const user = userEvent.setup();

    useDatasetVersions.mockReturnValue({
      data: versions,
      isLoading: false,
      isError: false,
    });

    renderPage();

    await user.click(screen.getByRole("button", { name: "View version 2" }));

    expect(screen.getByText("Version Detail Page")).toBeInTheDocument();
  });
});
