import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, useParams } from "react-router-dom";
import { DatasetCaseListPage } from "../../../features/datasetCases/DatasetCaseListPage";
import { useDatasetCases } from "../../../features/datasetCases/hooks";
import { useDatasetVersion } from "../../../features/datasetVersions/hooks";
import { useDataset } from "../../../features/datasets/hooks";
import type { DatasetVersion } from "../../../features/datasetVersions/api";

vi.mock("react-router-dom", async () => {
  const actual =
    await vi.importActual<typeof import("react-router-dom")>(
      "react-router-dom",
    );

  return {
    ...actual,
    useParams: vi.fn(),
  };
});

vi.mock("../../../features/datasetCases/hooks", () => ({
  useDatasetCases: vi.fn(),
  useCreateDatasetCase: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useUpdateDatasetCase: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useDeleteDatasetCase: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
}));

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useDatasetVersion: vi.fn(),
}));

vi.mock("../../../features/datasets/hooks", () => ({
  useDataset: vi.fn(),
}));

const mockedUseParams = vi.mocked(useParams);
const mockedUseDatasetCases = vi.mocked(useDatasetCases);
const mockedUseDatasetVersion = vi.mocked(useDatasetVersion);
const mockedUseDataset = vi.mocked(useDataset);

const dataset = {
  id: "dataset-1",
  project_id: "project-1",
  name: "RAG Evaluation",
  slug: "rag-evaluation",
  description: "RAG evaluation dataset",
  dataset_type: "rag" as const,
  is_active: true,
};

const draftVersion: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 1,
  status: "draft",
  description: "Draft version",
  case_count: 2,
  analytics: null,
  is_active: true,
};

const readyVersion: DatasetVersion = {
  ...draftVersion,
  status: "ready" as const,
};

const datasetCases = [
  {
    id: "case-1",
    dataset_version_id: "version-1",
    input: "What is RAG?",
    expected_output: "Retrieval augmented generation.",
    case_metadata: null,
    has_reference: true,
    has_context: true,
    position: 0,
    is_active: true,
  },
  {
    id: "case-2",
    dataset_version_id: "version-1",
    input: "What are embeddings?",
    expected_output: "Vector representations.",
    case_metadata: null,
    has_reference: false,
    has_context: false,
    position: 1,
    is_active: true,
  },
];

function mockLoadedState(
  version: DatasetVersion = draftVersion,
  cases = datasetCases,
) {
  mockedUseParams.mockReturnValue({
    datasetId: "dataset-1",
    versionId: "version-1",
  });

  mockedUseDataset.mockReturnValue({
    data: dataset,
    isLoading: false,
    isError: false,
  } as never);

  mockedUseDatasetVersion.mockReturnValue({
    data: version,
    isLoading: false,
    isError: false,
  } as never);

  mockedUseDatasetCases.mockReturnValue({
    data: cases,
    isLoading: false,
    isError: false,
  } as never);
}

function renderPage() {
  return render(
    <MemoryRouter>
      <DatasetCaseListPage />
    </MemoryRouter>,
  );
}

describe("DatasetCaseListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows an error when dataset version parameters are missing", () => {
    mockedUseParams.mockReturnValue({});

    mockedUseDataset.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetCases.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    expect(() => renderPage()).not.toThrow();

    expect(
      screen.getByText("Dataset version information is missing."),
    ).toBeInTheDocument();
  });

  it("shows loading state while the version is loading", () => {
    mockedUseParams.mockReturnValue({
      datasetId: "dataset-1",
      versionId: "version-1",
    });

    mockedUseDataset.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as never);

    mockedUseDatasetCases.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as never);

    renderPage();

    expect(screen.getByText("Loading dataset cases...")).toBeInTheDocument();
  });

  it("shows loading state while cases are loading", () => {
    mockedUseParams.mockReturnValue({
      datasetId: "dataset-1",
      versionId: "version-1",
    });

    mockedUseDataset.mockReturnValue({
      data: dataset,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetVersion.mockReturnValue({
      data: draftVersion,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetCases.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as never);

    renderPage();

    expect(screen.getByText("Loading dataset cases...")).toBeInTheDocument();
  });

  it("shows error state when loading fails", () => {
    mockedUseParams.mockReturnValue({
      datasetId: "dataset-1",
      versionId: "version-1",
    });

    mockedUseDataset.mockReturnValue({
      data: dataset,
      isLoading: false,
      isError: false,
    } as never);

    mockedUseDatasetVersion.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as never);

    mockedUseDatasetCases.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as never);

    renderPage();

    expect(
      screen.getByText("Unable to load dataset cases."),
    ).toBeInTheDocument();
  });

  it("renders draft cases and Add Case action", () => {
    mockLoadedState();

    renderPage();

    expect(screen.getByRole("heading", { name: "Cases" })).toBeInTheDocument();
    expect(
      screen.getByText("Manage evaluation cases for Dataset Version v1."),
    ).toBeInTheDocument();

    expect(screen.getByText("What is RAG?")).toBeInTheDocument();
    expect(screen.getByText("What are embeddings?")).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Add Case" }),
    ).toBeInTheDocument();
  });

  it("shows empty draft state with Add Case action", () => {
    mockLoadedState(draftVersion, []);

    renderPage();

    expect(screen.getByText("No cases yet")).toBeInTheDocument();
    expect(
      screen.getByText("Add the first case to this draft dataset version."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add Case" }),
    ).toBeInTheDocument();
  });

  it("does not show Add Case for a ready version", () => {
    mockLoadedState(readyVersion);

    renderPage();

    expect(
      screen.queryByRole("button", { name: "Add Case" }),
    ).not.toBeInTheDocument();
  });

  it("shows the ready version case columns", () => {
    mockLoadedState(readyVersion);

    renderPage();

    expect(screen.getByText("Reference")).toBeInTheDocument();
    expect(screen.getByText("Context")).toBeInTheDocument();

    expect(screen.getByLabelText("Reference available")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Reference not available"),
    ).toBeInTheDocument();
  });

  it("opens the Add Case dialog from the page action", async () => {
    const user = userEvent.setup();

    mockLoadedState();

    renderPage();

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(
      screen.getByRole("dialog", { name: "Add Dataset Case" }),
    ).toBeInTheDocument();
  });

  it("sorts cases when a sortable column is clicked", async () => {
    const user = userEvent.setup();

    mockLoadedState();

    renderPage();

    expect(screen.getByText("What is RAG?")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Input" }));

    const rows = screen.getAllByRole("row");

    expect(rows[1]).toHaveTextContent("What are embeddings?");
    expect(rows[2]).toHaveTextContent("What is RAG?");
  });
});
