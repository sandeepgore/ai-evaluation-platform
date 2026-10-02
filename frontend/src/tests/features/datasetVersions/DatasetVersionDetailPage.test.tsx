import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionDetailPage } from "../../../features/datasetVersions/DatasetVersionDetailPage";
import type { DatasetVersion } from "../../../features/datasetVersions/api";
import { useDataset } from "../../../features/datasets/hooks";
import { useDatasetVersion } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useDatasetVersion: vi.fn(),
}));

vi.mock("../../../features/datasets/hooks", () => ({
  useDataset: vi.fn(),
}));

const mockedUseDatasetVersion = vi.mocked(useDatasetVersion);
const mockedUseDataset = vi.mocked(useDataset);

const version: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 2,
  status: "ready",
  description: "Production evaluation version",
  case_count: 25,
  analytics: null,
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

    mockedUseDataset.mockReturnValue({
      data: {
        id: "dataset-1",
        name: "RAG Evaluation",
      },
      isLoading: false,
      isError: false,
    } as never);
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

  it("tells the user to finalize a draft version before analytics are available", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: {
        ...version,
        status: "draft",
        analytics: {
          case_count: 25,
          reference_count: 20,
          context_count: 15,
          reference_coverage: 0.8,
          context_coverage: 0.6,
        },
      },
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(
      screen.getByText(/Analytics are not available yet/i),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        /Finalize the version to generate and view reference and context analytics/i,
      ),
    ).toBeInTheDocument();
  });

  it("does not display reference or context analytics cards for a draft version", () => {
    mockedUseDatasetVersion.mockReturnValue({
      data: {
        ...version,
        status: "draft",
        analytics: {
          case_count: 25,
          reference_count: 20,
          context_count: 15,
          reference_coverage: 0.8,
          context_coverage: 0.6,
        },
      },
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(screen.queryByText("Reference Data")).not.toBeInTheDocument();
    expect(screen.queryByText("Context Data")).not.toBeInTheDocument();
  });
});
