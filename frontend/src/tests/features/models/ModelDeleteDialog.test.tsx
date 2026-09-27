import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelDeleteDialog } from "../../../features/models/ModelDeleteDialog";
import type { Model } from "../../../features/models/api";

const mutateAsync = vi.fn();

vi.mock("../../../features/models/hooks", () => ({
  useDeleteModel: () => ({
    mutateAsync,
    isPending: false,
  }),
}));

const model: Model = {
  id: "model-1",
  project_id: "project-1",
  name: "GPT-4o",
  provider: "openai",
  model_identifier: "gpt-4o",
  model_type: "chat",
  configuration: null,
  input_price_per_million: 2.5,
  output_price_per_million: 10,
  pricing_currency: "USD",
  is_active: true,
};

describe("ModelDeleteDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(undefined);
  });

  it("renders the delete confirmation", () => {
    render(<ModelDeleteDialog open model={model} onClose={vi.fn()} />);

    expect(
      screen.getByRole("heading", { name: "Delete Model" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("dialog")).toHaveTextContent(
      "Are you sure you want to delete GPT-4o? This action cannot be undone.",
    );

    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("deletes the selected model and closes the dialog", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(<ModelDeleteDialog open model={model} onClose={onClose} />);

    await user.click(screen.getByRole("button", { name: "Delete" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith("model-1");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("disables delete when no model is selected", () => {
    render(<ModelDeleteDialog open model={null} onClose={vi.fn()} />);

    expect(screen.getByRole("button", { name: "Delete" })).toBeDisabled();
  });
});
