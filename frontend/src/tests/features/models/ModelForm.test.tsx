import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ModelForm } from "../../../features/models/ModelForm";
import type { Model } from "../../../features/models/api";

function renderForm(onSubmit = vi.fn(), onCancel = vi.fn(), model?: Model) {
  const queryClient = new QueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <ModelForm model={model} onSubmit={onSubmit} onCancel={onCancel} />
    </QueryClientProvider>,
  );
}

describe("ModelForm", () => {
  it("renders the model fields", () => {
    renderForm();

    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Model Identifier")).toBeInTheDocument();
    expect(screen.getByLabelText("Configuration")).toBeInTheDocument();
    expect(screen.getByLabelText("Input Price / 1M")).toBeInTheDocument();
    expect(screen.getByLabelText("Output Price / 1M")).toBeInTheDocument();
    expect(screen.getByLabelText("Currency")).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Create Model" }),
    ).toBeInTheDocument();
  });

  it("shows validation errors for required fields", async () => {
    const user = userEvent.setup();

    renderForm();

    await user.click(screen.getByRole("button", { name: "Create Model" }));

    expect(await screen.findByText("Name is required")).toBeInTheDocument();

    expect(
      await screen.findByText("Model identifier is required"),
    ).toBeInTheDocument();

    expect(await screen.findByText("Provider is required")).toBeInTheDocument();
  });

  it("rejects invalid configuration JSON", async () => {
    const user = userEvent.setup();

    renderForm();

    await user.type(screen.getByLabelText("Name"), "Test Model");

    await user.type(screen.getByLabelText("Model Identifier"), "test-model");

    await user.click(screen.getByRole("combobox", { name: "Provider" }));
    await user.click(screen.getByRole("option", { name: "OpenAI" }));

    await user.clear(screen.getByLabelText("Configuration"));

    await user.type(screen.getByLabelText("Configuration"), "not-json");

    await user.click(screen.getByRole("button", { name: "Create Model" }));

    expect(
      await screen.findByText("Configuration must be a valid JSON object"),
    ).toBeInTheDocument();
  });

  it("submits configuration as an object", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    renderForm(onSubmit);

    await user.type(screen.getByLabelText("Name"), "Test Model");

    await user.type(screen.getByLabelText("Model Identifier"), "test-model");

    await user.click(screen.getByRole("combobox", { name: "Provider" }));
    await user.click(screen.getByRole("option", { name: "OpenAI" }));

    await user.click(screen.getByLabelText("Configuration"));
    await user.paste('{ "temperature": 0.2 }');

    await user.click(screen.getByRole("button", { name: "Create Model" }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: "Test Model",
      provider: "openai",
      model_identifier: "test-model",
      model_type: "chat",
      configuration: {
        temperature: 0.2,
      },
      input_price_per_million: 0,
      output_price_per_million: 0,
      pricing_currency: "USD",
    });
  });

  it("loads existing model values in edit mode", () => {
    const model: Model = {
      id: "model-1",
      project_id: "project-1",
      name: "Existing Model",
      provider: "ollama",
      model_identifier: "llama3.2:3b",
      model_type: "chat",
      configuration: {
        temperature: 0.1,
      },
      input_price_per_million: 1.5,
      output_price_per_million: 2.5,
      pricing_currency: "USD",
      is_active: true,
    };

    renderForm(vi.fn(), vi.fn(), model);

    expect(screen.getByLabelText("Name")).toHaveValue("Existing Model");
    expect(screen.getByLabelText("Model Identifier")).toHaveValue(
      "llama3.2:3b",
    );
    expect(screen.getByLabelText("Configuration")).toHaveValue(
      '{\n  "temperature": 0.1\n}',
    );
    expect(screen.getByLabelText("Input Price / 1M")).toHaveValue(1.5);
    expect(screen.getByLabelText("Output Price / 1M")).toHaveValue(2.5);
    expect(screen.getByLabelText("Currency")).toHaveValue("USD");
  });
});
