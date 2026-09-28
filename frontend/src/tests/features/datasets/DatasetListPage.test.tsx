import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetListPage } from "../../../features/datasets/DatasetListPage";
import type { Dataset } from "../../../features/datasets/api";

const useDatasets = vi.fn();
const useAppContextStore = vi.fn();

vi.mock(
  "../../../features/datasets/hooks",
  () => ({
    useDatasets: (projectId: string | null) =>
      useDatasets(projectId),
  }),
);

vi.mock(
  "../../../store/appContextStore",
  () => ({
    useAppContextStore: (selector: (state: unknown) => unknown) =>
      useAppContextStore(selector),
  }),
);

vi.mock(
  "../../../features/datasets/DatasetCreateDialog",
  () => ({
    DatasetCreateDialog: ({
      open,
      projectId,
    }: {
      open: boolean;
      projectId: string;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Create Dataset Dialog: {projectId}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/datasets/DatasetEditDialog",
  () => ({
    DatasetEditDialog: ({
      open,
      dataset,
    }: {
      open: boolean;
      dataset: Dataset | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Edit Dataset Dialog: {dataset?.name}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/datasets/DatasetDeleteDialog",
  () => ({
    DatasetDeleteDialog: ({
      open,
      dataset,
    }: {
      open: boolean;
      dataset: Dataset | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Delete Dataset Dialog: {dataset?.name}
        </div>
      ) : null,
  }),
);

const datasets: Dataset[] = [
  {
    id: "dataset-1",
    project_id: "project-1",
    name: "RAG Evaluation",
    slug: "rag-evaluation",
    description: "RAG evaluation dataset",
    dataset_type: "rag",
    is_active: true,
  },
];

describe("DatasetListPage", () => {
  beforeEach(() => {
    useDatasets.mockReset();
    useAppContextStore.mockReset();

    useAppContextStore.mockImplementation(
      (selector: (state: unknown) => unknown) =>
        selector({
          selectedProjectId: "project-1",
        }),
    );
  });

  it("renders the no-project state", () => {
    useAppContextStore.mockImplementation(
      (selector: (state: unknown) => unknown) =>
        selector({
          selectedProjectId: null,
        }),
    );

    useDatasets.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    expect(screen.getByText("No project selected")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Select a project from the Dashboard to view its datasets.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    useDatasets.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<DatasetListPage />);

    expect(screen.getByText("Loading datasets...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    useDatasets.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<DatasetListPage />);

    expect(
      screen.getByText("Unable to load datasets."),
    ).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    useDatasets.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    expect(screen.getByText("No datasets yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first dataset for this project to get started.",
      ),
    ).toBeInTheDocument();
  });

  it("renders datasets", () => {
    useDatasets.mockReturnValue({
      data: datasets,
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    expect(screen.getByText("RAG Evaluation")).toBeInTheDocument();
    expect(screen.getByText("rag-evaluation")).toBeInTheDocument();
  });

  it("opens the create dialog with the selected project", async () => {
    const user = userEvent.setup();

    useDatasets.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    await user.click(
      screen.getByRole("button", { name: "Create Dataset" }),
    );

    expect(
      screen.getByText("Create Dataset Dialog: project-1"),
    ).toBeInTheDocument();
  });

  it("opens the edit dialog for the selected dataset", async () => {
    const user = userEvent.setup();

    useDatasets.mockReturnValue({
      data: datasets,
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    await user.click(
      screen.getByRole("button", { name: "Edit RAG Evaluation" }),
    );

    expect(
      screen.getByText("Edit Dataset Dialog: RAG Evaluation"),
    ).toBeInTheDocument();
  });

  it("opens the delete dialog for the selected dataset", async () => {
    const user = userEvent.setup();

    useDatasets.mockReturnValue({
      data: datasets,
      isLoading: false,
      isError: false,
    });

    render(<DatasetListPage />);

    await user.click(
      screen.getByRole("button", { name: "Delete RAG Evaluation" }),
    );

    expect(
      screen.getByText("Delete Dataset Dialog: RAG Evaluation"),
    ).toBeInTheDocument();
  });
});
