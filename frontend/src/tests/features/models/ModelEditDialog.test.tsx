import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ModelEditDialog } from "../../../features/models/ModelEditDialog";
import type { Model } from "../../../features/models/api";

const mutateAsync = vi.fn();

vi.mock("../../../features/models/hooks", () => ({
  useUpdateModel: () => ({
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
  configuration: {
    temperature: 0.2,
  },
  input_price_per_million: 2.5,
  output_price_per_million: 10,
  pricing_currency: "USD",
  is_active: true,
};

describe("ModelEditDialog", () => {
  beforeEach(() => {
    mutateAsync.mockReset();
    mutateAsync.mockResolvedValue(model);
  });

  it("renders existing model values", () => {
    render(
      <ModelEditDialog
        open
        model={model}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByLabelText("Name")).toHaveValue("GPT-4o");
    expect(
      screen.getByLabelText("Model Identifier"),
    ).toHaveValue("gpt-4o");
    expect(
      screen.getByLabelText("Configuration"),
    ).toHaveValue('{\n  "temperature": 0.2\n}');
    expect(
      screen.getByLabelText("Input Price / 1M"),
    ).toHaveValue(2.5);
    expect(
      screen.getByLabelText("Output Price / 1M"),
    ).toHaveValue(10);
    expect(
      screen.getByLabelText("Currency"),
    ).toHaveValue("USD");

    expect(
      screen.getByRole("heading", { name: "Edit Model" }),
    ).toBeInTheDocument();
  });

  it("updates the model without changing its project", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <ModelEditDialog
        open
        model={model}
        onClose={onClose}
      />,
    );

    const nameInput = screen.getByLabelText("Name");

    await user.clear(nameInput);
    await user.type(nameInput, "GPT-4o Updated");

    await user.click(
      screen.getByRole("button", { name: "Save Changes" }),
    );

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      modelId: "model-1",
      payload: {
        name: "GPT-4o Updated",
        provider: "openai",
        model_identifier: "gpt-4o",
        model_type: "chat",
        configuration: {
          temperature: 0.2,
        },
        input_price_per_million: 2.5,
        output_price_per_million: 10,
        pricing_currency: "USD",
      },
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders no form when no model is selected", () => {
    render(
      <ModelEditDialog
        open
        model={null}
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Edit Model" }),
    ).toBeInTheDocument();

    expect(
      screen.queryByLabelText("Name"),
    ).not.toBeInTheDocument();
  });
});
