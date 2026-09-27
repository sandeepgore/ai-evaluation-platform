import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProjectTable } from "../../../features/projects/ProjectTable";
import type { Project } from "../../../features/projects/api";

const projects: Project[] = [
  {
    id: "project-1",
    organization_id: "org-1",
    name: "AI Evaluation",
    slug: "ai-evaluation",
    description: "Evaluation platform project",
    is_active: true,
  },
  {
    id: "project-2",
    organization_id: "org-1",
    name: "Archived Project",
    slug: "archived-project",
    description: null,
    is_active: false,
  },
];

describe("ProjectTable", () => {
  it("renders project information", () => {
    render(
      <ProjectTable
        projects={projects}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("AI Evaluation")).toBeInTheDocument();
    expect(screen.getByText("ai-evaluation")).toBeInTheDocument();
    expect(
      screen.getByText("Evaluation platform project"),
    ).toBeInTheDocument();

    expect(screen.getByText("Archived Project")).toBeInTheDocument();
    expect(screen.getByText("archived-project")).toBeInTheDocument();
    expect(screen.getByText("No description")).toBeInTheDocument();
  });

  it("renders project status", () => {
    render(
      <ProjectTable
        projects={projects}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  it("calls onEdit with the selected project", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <ProjectTable
        projects={projects}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Edit AI Evaluation" }),
    );

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(projects[0]);
  });

  it("calls onDelete with the selected project", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <ProjectTable
        projects={projects}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Delete AI Evaluation" }),
    );

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(projects[0]);
  });
});