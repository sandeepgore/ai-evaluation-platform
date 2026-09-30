import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionDetailPage } from "../../../features/datasetVersions/DatasetVersionDetailPage";
import type { DatasetVersion } from "../../../features/datasetVersions/api";
import { useDatasetVersion } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useDatasetVersion: vi.fn(),
}));

const mockedUseDatasetVersion = vi.mocked(useDatasetVersion);

const version: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 2,
  status: "ready",
  description: "Production evaluation version",
  case_count: 25,
  is_active: true,
};

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/datasets/dataset-1/versions/version-1"]}>
      <Routes>
        <Route
          path="/datasets/:datasetId/versions/:versionId"
          element={<DatasetVersionDetailPage />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("DatasetVersionDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the missing version ID state", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    render(
      <MemoryRouter>
        <DatasetVersionDetailPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Dataset version ID is missing."),
    ).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as never);

    renderPage();

    expect(screen.getByText("Loading dataset version...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as never);

    renderPage();

    expect(
      screen.getByText("Unable to load dataset version."),
    ).toBeInTheDocument();
  });

  it("renders the dataset version details", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: version,
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(screen.getByText("Dataset Version v2")).toBeInTheDocument();

    expect(
      screen.getByText("Production evaluation version"),
    ).toBeInTheDocument();
  });

  it("renders the fallback description when description is null", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: {
        ...version,
        description: null,
      },
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(screen.getByText("No description")).toBeInTheDocument();
  });

  it("uses the version ID when loading the version", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: version,
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(mockedUseDatasetVersion).toHaveBeenCalledWith("version-1");
  });
});


