import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProjectListPage } from "../../../features/projects/ProjectListPage";
import type { Project } from "../../../features/projects/api";

const useProjects = vi.fn();
const useAppContextStore = vi.fn();

vi.mock(
  "../../../features/projects/hooks",
  () => ({
    useProjects: (organizationId: string | null) =>
      useProjects(organizationId),
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
  "../../../features/projects/ProjectCreateDialog",
  () => ({
    ProjectCreateDialog: ({
      open,
      organizationId,
    }: {
      open: boolean;
      organizationId: string;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Create Project Dialog: {organizationId}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/projects/ProjectEditDialog",
  () => ({
    ProjectEditDialog: ({
      open,
      project,
    }: {
      open: boolean;
      project: Project | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Edit Project Dialog: {project?.name}
        </div>
      ) : null,
  }),
);

vi.mock(
  "../../../features/projects/ProjectDeleteDialog",
  () => ({
    ProjectDeleteDialog: ({
      open,
      project,
    }: {
      open: boolean;
      project: Project | null;
      onClose: () => void;
    }) =>
      open ? (
        <div role="dialog">
          Delete Project Dialog: {project?.name}
        </div>
      ) : null,
  }),
);

const projects: Project[] = [
  {
    id: "project-1",
    organization_id: "org-1",
    name: "AI Evaluation",
    slug: "ai-evaluation",
    description: "Evaluation platform project",
    is_active: true,
  },
];

describe("ProjectListPage", () => {
  beforeEach(() => {
    useProjects.mockReset();
    useAppContextStore.mockReset();

    useAppContextStore.mockImplementation(
      (selector: (state: unknown) => unknown) =>
        selector({
          selectedOrganizationId: "org-1",
        }),
    );
  });

  it("renders the no-organization state", () => {
    useAppContextStore.mockImplementation(
      (selector: (state: unknown) => unknown) =>
        selector({
          selectedOrganizationId: null,
        }),
    );

    useProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    expect(screen.getByText("No organization selected")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Select an organization from the Dashboard to view its projects.",
      ),
    ).toBeInTheDocument();
  });

  it("renders the loading state", () => {
    useProjects.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    });

    render(<ProjectListPage />);

    expect(screen.getByText("Loading projects...")).toBeInTheDocument();
  });

  it("renders the error state", () => {
    useProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    });

    render(<ProjectListPage />);

    expect(
      screen.getByText("Unable to load projects."),
    ).toBeInTheDocument();
  });

  it("renders the empty state", () => {
    useProjects.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    expect(screen.getByText("No projects yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Create your first project for this organization to get started.",
      ),
    ).toBeInTheDocument();
  });

  it("renders projects", () => {
    useProjects.mockReturnValue({
      data: projects,
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    expect(screen.getByText("AI Evaluation")).toBeInTheDocument();
    expect(screen.getByText("ai-evaluation")).toBeInTheDocument();
  });

  it("opens the create dialog with the selected organization", async () => {
    const user = userEvent.setup();

    useProjects.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    await user.click(
      screen.getByRole("button", { name: "Create Project" }),
    );

    expect(
      screen.getByText("Create Project Dialog: org-1"),
    ).toBeInTheDocument();
  });

  it("opens the edit dialog for the selected project", async () => {
    const user = userEvent.setup();

    useProjects.mockReturnValue({
      data: projects,
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    await user.click(
      screen.getByRole("button", { name: "Edit AI Evaluation" }),
    );

    expect(
      screen.getByText("Edit Project Dialog: AI Evaluation"),
    ).toBeInTheDocument();
  });

  it("opens the delete dialog for the selected project", async () => {
    const user = userEvent.setup();

    useProjects.mockReturnValue({
      data: projects,
      isLoading: false,
      isError: false,
    });

    render(<ProjectListPage />);

    await user.click(
      screen.getByRole("button", { name: "Delete AI Evaluation" }),
    );

    expect(
      screen.getByText("Delete Project Dialog: AI Evaluation"),
    ).toBeInTheDocument();
  });
});