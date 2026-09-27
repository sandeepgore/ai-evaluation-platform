import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModelListPage } from "../../../features/models/ModelListPage";
import type { Model } from "../../../features/models/api";

const useModels = vi.fn();
const useAppContextStore = vi.fn();

vi.mock(
  "../../../features/models/hooks",
  () => ({
    useModels: (projectId: string | null) =>
      useModels(projectId),
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
  "../../../features/models/ModelCreateDialog",
  () => ({
    ModelCreateDialog: ({
      open,
      projectId,
    }: {
      open: boolean;
      projectId: string;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Create Model Dialog: {projectId}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/models/ModelEditDialog",
  () => ({
    ModelEditDialog: ({
      open,
      model,
    }: {
      open: boolean;
      model: Model | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Edit Model Dialog: {model?.name}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/models/ModelDeleteDialog",
  () => ({
    ModelDeleteDialog: ({
      open,
      model,
    }: {
      open: boolean;
      model: Model | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Delete Model Dialog: {model?.name}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/models/ModelTable",
  () => ({
    ModelTable: ({
      models,
      onEdit,
      onDelete,
    }: {
      models: Model[];
      onEdit: (model: Model) => void;
      onDelete: (model: Model) => void;
    }) => (
      <div>
        {models.map((model) => (
          <div key={model.id}>
            <span>{model.name}</span>
            <button onClick={() => onEdit(model)}>
              Edit {model.name}
            </button>
            <button onClick={() => onDelete(model)}>
              Delete {model.name}
            </button>
          </div>
        ))}
      </div>
    ),
  }),
);

const models: Model[] = [
  {
    id: "model-1",
    project_id: "project-1",
    name: "GPT-4o",
    provider: "openai",
    model_identifier: "gpt-4o",
    model_type: "chat",
    configuration: {
      temperature: 0.2,
    },
    input_price_per_million: 2.5,
    output_price_per_million: 10,
    pricing_currency: "USD",
    is_active: true,
  },
];

describe("ModelListPage", () => {
  beforeEach(() => {
    useModels.mockReset();
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

    useModels.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    expect(screen.getByText("No project selected")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Select a project from the Dashboard to view its models.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    useModels.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<ModelListPage />);

    expect(screen.getByText("Loading models...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    useModels.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<ModelListPage />);

    expect(
      screen.getByText("Unable to load models."),
    ).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    useModels.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    expect(screen.getByText("No models yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first model for this project to get started.",
      ),
    ).toBeInTheDocument();
  });

  it("renders models", () => {
    useModels.mockReturnValue({
      data: models,
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
  });

  it("opens the create dialog with the selected project", async () => {
    const user = userEvent.setup();

    useModels.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    await user.click(
      screen.getByRole("button", { name: "Create Model" }),
    );

    expect(
      screen.getByText("Create Model Dialog: project-1"),
    ).toBeInTheDocument();
  });

  it("opens the edit dialog for the selected model", async () => {
    const user = userEvent.setup();

    useModels.mockReturnValue({
      data: models,
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    await user.click(
      screen.getByRole("button", { name: "Edit GPT-4o" }),
    );

    expect(
      screen.getByText("Edit Model Dialog: GPT-4o"),
    ).toBeInTheDocument();
  });

  it("opens the delete dialog for the selected model", async () => {
    const user = userEvent.setup();

    useModels.mockReturnValue({
      data: models,
      isLoading: false,
      isError: false,
    });

    render(<ModelListPage />);

    await user.click(
      screen.getByRole("button", { name: "Delete GPT-4o" }),
    );

    expect(
      screen.getByText("Delete Model Dialog: GPT-4o"),
    ).toBeInTheDocument();
  });
});
