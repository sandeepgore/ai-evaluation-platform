import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelTable } from "../../../features/models/ModelTable";
import type { Model } from "../../../features/models/api";

const model: Model = {
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
};

describe("ModelTable", () => {
  it("renders model information", () => {
    render(
      <ModelTable
        models={[model]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
    expect(screen.getByText("OpenAI")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.getByText("USD 2.5 / 10")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("calls onEdit for the selected model", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();

    render(
      <ModelTable
        models={[model]}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", {
      name: "Edit GPT-4o",
    }));

    expect(onEdit).toHaveBeenCalledTimes(1);
    expect(onEdit).toHaveBeenCalledWith(model);
  });

  it("calls onDelete for the selected model", async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();

    render(
      <ModelTable
        models={[model]}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );

    await user.click(screen.getByRole("button", {
      name: "Delete GPT-4o",
    }));

    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onDelete).toHaveBeenCalledWith(model);
  });

  it("renders multiple models", () => {
    const secondModel: Model = {
      ...model,
      id: "model-2",
      name: "Claude",
      provider: "anthropic",
      model_identifier: "claude-sonnet",
    };

    render(
      <ModelTable
        models={[model, secondModel]}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );

    expect(screen.getByText("GPT-4o")).toBeInTheDocument();
    expect(screen.getByText("Claude")).toBeInTheDocument();
    expect(screen.getByText("Anthropic")).toBeInTheDocument();
  });
});
