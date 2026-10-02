import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetVersionForm } from "../../../features/datasetVersions/DatasetVersionForm";
import type { DatasetVersion } from "../../../features/datasetVersions/api";

const version: DatasetVersion = {
  id: "version-1",
  dataset_id: "dataset-1",
  version: 3,
  status: "draft",
  description: "Existing description",
  case_count: 0,
  analytics: null,
  is_active: true,
};

describe("DatasetVersionForm", () => {
  it("renders create form fields", () => {
    render(<DatasetVersionForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(
      screen.getByRole("textbox", { name: "Description" }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Create Version" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("submits create values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<DatasetVersionForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(
      screen.getByRole("textbox", { name: "Description" }),
      "New version",
    );

    await user.click(screen.getByRole("button", { name: "Create Version" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      { description: "New version" },
      expect.anything(),
    );
  });

  it("renders edit mode without the version field", () => {
    render(
      <DatasetVersionForm
        version={version}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("spinbutton", { name: "Version" }),
    ).not.toBeInTheDocument();

    expect(screen.getByRole("textbox", { name: "Description" })).toHaveValue(
      "Existing description",
    );

    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("submits edited description", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <DatasetVersionForm
        version={version}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    const description = screen.getByRole("textbox", {
      name: "Description",
    });

    await user.clear(description);
    await user.type(description, "Updated description");

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      { description: "Updated description" },
      expect.anything(),
    );
  });

  it("calls onCancel", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(<DatasetVersionForm onSubmit={vi.fn()} onCancel={onCancel} />);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables fields and actions while submitting", () => {
    render(
      <DatasetVersionForm submitting onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.getByRole("textbox", { name: "Description" })).toBeDisabled();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
