import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelCreateDialog } from "../../../features/models/ModelCreateDialog";

const mutateAsync = vi.fn();

vi.mock("../../../features/models/hooks", () => ({
  useCreateModel: () => ({
    mutateAsync,
    isPending: false,
  }),
}));

describe("ModelCreateDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue({
      id: "model-1",
      project_id: "project-1",
      name: "GPT-4o",
    });
  });

  it("renders the create dialog", () => {
    render(
      <ModelCreateDialog
        open
        projectId="project-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Create Model" }),
    ).toBeInTheDocument();

    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Model Identifier"),
    ).toBeInTheDocument();
  });

  it("creates a model with the selected project", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ModelCreateDialog
        open
        projectId="project-1"
        onClose={onClose}
      />,
    );

    await user.type(screen.getByLabelText("Name"), "GPT-4o");
    await user.click(screen.getByLabelText("Provider"));
    await user.click(screen.getByRole("option", { name: "OpenAI" }));

    await user.type(
      screen.getByLabelText("Model Identifier"),
      "gpt-4o",
    );

    await user.click(
      screen.getByRole("button", { name: "Create Model" }),
    );

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      project_id: "project-1",
      name: "GPT-4o",
      provider: "openai",
      model_identifier: "gpt-4o",
      model_type: "chat",
      configuration: null,
      input_price_per_million: 0,
      output_price_per_million: 0,
      pricing_currency: "USD",
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
