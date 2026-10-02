import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { DatasetCaseForm } from "../../../features/datasetCases/DatasetCaseForm";
import type { DatasetCase } from "../../../features/datasetCases/api";

const datasetCase: DatasetCase = {
  id: "case-1",
  dataset_version_id: "version-1",
  input: "Existing input",
  expected_output: "Existing output",
  case_metadata: {
    category: "rag",
  },
  has_reference: true,
  has_context: true,
  position: 0,
  is_active: true,
};

describe("DatasetCaseForm", () => {
  it("renders create form fields", () => {
    render(<DatasetCaseForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Input" })).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Expected Output" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Metadata (JSON)" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add Case" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("submits create values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<DatasetCaseForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(
      screen.getByRole("textbox", { name: "Input" }),
      "New input",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Expected Output" }),
      "New output",
    );
    const metadata = screen.getByRole("textbox", {
      name: "Metadata (JSON)",
    });

    await user.click(metadata);
    await user.paste('{"category":"rag"}');

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      {
        input: "New input",
        expected_output: "New output",
        case_metadata: '{"category":"rag"}',
      },
      expect.anything(),
    );
  });

  it("shows validation error when input is empty", async () => {
    const user = userEvent.setup();

    render(<DatasetCaseForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(await screen.findByText("Input is required")).toBeInTheDocument();
  });

  it("shows validation error for invalid metadata JSON", async () => {
    const user = userEvent.setup();

    render(<DatasetCaseForm onSubmit={vi.fn()} onCancel={vi.fn()} />);

    await user.type(
      screen.getByRole("textbox", { name: "Input" }),
      "Test input",
    );
    await user.type(
      screen.getByRole("textbox", { name: "Metadata (JSON)" }),
      "not-json",
    );

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(
      await screen.findByText(
        "Metadata must be valid JSON containing an object.",
      ),
    ).toBeInTheDocument();
  });

  it("accepts empty metadata", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<DatasetCaseForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    await user.type(
      screen.getByRole("textbox", { name: "Input" }),
      "Test input",
    );

    await user.click(screen.getByRole("button", { name: "Add Case" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("renders edit mode with existing values", () => {
    render(
      <DatasetCaseForm
        datasetCase={datasetCase}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Input" })).toHaveValue(
      "Existing input",
    );
    expect(
      screen.getByRole("textbox", { name: "Expected Output" }),
    ).toHaveValue("Existing output");
    expect(
      screen.getByRole("textbox", { name: "Metadata (JSON)" }),
    ).toHaveValue('{\n  "category": "rag"\n}');
    expect(
      screen.getByRole("button", { name: "Save Changes" }),
    ).toBeInTheDocument();
  });

  it("submits edited values", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(
      <DatasetCaseForm
        datasetCase={datasetCase}
        onSubmit={onSubmit}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByRole("textbox", { name: "Input" });

    await user.clear(input);
    await user.type(input, "Updated input");

    await user.click(screen.getByRole("button", { name: "Save Changes" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      {
        input: "Updated input",
        expected_output: "Existing output",
        case_metadata: '{\n  "category": "rag"\n}',
      },
      expect.anything(),
    );
  });

  it("calls onCancel", async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();

    render(<DatasetCaseForm onSubmit={vi.fn()} onCancel={onCancel} />);

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("disables fields and actions while submitting", () => {
    render(
      <DatasetCaseForm submitting onSubmit={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.getByRole("textbox", { name: "Input" })).toBeDisabled();
    expect(
      screen.getByRole("textbox", { name: "Expected Output" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("textbox", { name: "Metadata (JSON)" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving..." })).toBeDisabled();
  });
});
