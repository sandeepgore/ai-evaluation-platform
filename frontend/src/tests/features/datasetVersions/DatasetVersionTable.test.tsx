import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetVersionTable } from "../../../features/datasetVersions/DatasetVersionTable";
import type { DatasetVersion } from "../../../features/datasetVersions/api";

const versions: DatasetVersion[] = [
  {
    id: "version-1",
    dataset_id: "dataset-1",
    version: 2,
    status: "ready",
    description: "Production evaluation dataset",
    case_count: 10,
    is_active: true,
  },
  {
    id: "version-2",
    dataset_id: "dataset-1",
    version: 1,
    status: "draft",
    description: null,
    case_count: 0,
    is_active: true,
  },
  {
    id: "version-3",
    dataset_id: "dataset-1",
    version: 3,
    status: "archived",
    description: "Archived version",
    case_count: 0,
    is_active: true,
  },
];

describe("DatasetVersionTable", () => {
  it("renders version information", () => {
    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(
      screen.getByText("Production evaluation dataset"),
    ).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();

    expect(screen.getByText("v1")).toBeInTheDocument();
    expect(screen.getByText("No description")).toBeInTheDocument();
    expect(screen.getAllByText("0")).toHaveLength(2);
  });

  it("renders version statuses", () => {
    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Archived")).toBeInTheDocument();
  });

  it("calls onView with the selected version", async () => {
    const user = userEvent.setup();
    const onView = vi.fn();

    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={onView}
      />,
    );

    await user.click(screen.getByRole("button", { name: "View version 2" }));

    expect(onView).toHaveBeenCalledTimes(1);
    expect(onView).toHaveBeenCalledWith(versions[0]);
  });

  it("calls onEdit with the selected version", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={onEdit}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Edit version 2" }));

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(versions[0]);
  });

  it("shows finalize only for draft versions", () => {
    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Finalize version 1" }),
    ).toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Finalize version 2" }),
    ).not.toBeInTheDocument();

    expect(
      screen.queryByRole("button", { name: "Finalize version 3" }),
    ).not.toBeInTheDocument();
  });

  it("calls onFinalize with the selected draft version", async () => {
    const user = userEvent.setup();
    const onFinalize = vi.fn();

    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={onFinalize}
        onView={vi.fn()}
      />,
    );

    await user.click(
      screen.getByRole("button", { name: "Finalize version 1" }),
    );

    expect(onFinalize).toHaveBeenCalledTimes(1);
    expect(onFinalize).toHaveBeenCalledWith(versions[1]);
  });

  it("allows delete for a version with no cases", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={onDelete}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    const deleteButton = screen.getByRole("button", {
      name: "Delete version 1",
    });

    expect(deleteButton).toBeEnabled();

    await user.click(deleteButton);

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(versions[1]);
  });

  it("disables delete for a version with cases", () => {
    render(
      <DatasetVersionTable
        versions={versions}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
        onFinalize={vi.fn()}
        onView={vi.fn()}
      />,
    );

    const deleteButton = screen.getByRole("button", {
      name: "Delete version 2",
    });

    expect(deleteButton).toBeDisabled();
  });
});
