import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DatasetVersionImportDialog } from "../../../features/datasetVersions/DatasetVersionImportDialog";
import { useImportDataset } from "../../../features/datasetVersions/hooks";

vi.mock("../../../features/datasetVersions/hooks", () => ({
  useImportDataset: vi.fn(),
}));

const mockedUseImportDataset = vi.mocked(useImportDataset);

function createJsonFile(content: string, name = "dataset.json") {
  return new File([content], name, {
    type: "application/json",
  });
}

describe("DatasetVersionImportDialog", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedUseImportDataset.mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({
        id: "version-1",
        dataset_id: "dataset-1",
        version: 1,
        status: "ready",
        description: null,
        case_count: 1,
        is_active: true,
      }),
      isPending: false,
    } as never);
  });

  it("renders when open", () => {
    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("dialog", { name: "Import Dataset JSON" }),
    ).toBeInTheDocument();

    expect(
      screen.getByText(
        "Upload a JSON file containing dataset cases. A new ready version will be created automatically.",
      ),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("button", { name: "Select JSON File" }),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Import JSON" })).toBeDisabled();
  });

  it("does not render when closed", () => {
    render(
      <DatasetVersionImportDialog
        open={false}
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.queryByRole("dialog", { name: "Import Dataset JSON" }),
    ).not.toBeInTheDocument();
  });

  it("rejects invalid JSON", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(input, createJsonFile("{ invalid json"));

    expect(screen.getByRole("alert")).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Import JSON" })).toBeDisabled();
  });

  it("rejects a JSON root that is not an object", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(input, createJsonFile(JSON.stringify([])));

    expect(
      await screen.findByText("JSON root must be an object."),
    ).toBeInTheDocument();
  });

  it("rejects JSON without cases", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(input, createJsonFile(JSON.stringify({ cases: [] })));

    expect(
      await screen.findByText("JSON must contain a non-empty cases array."),
    ).toBeInTheDocument();
  });

  it("rejects unexpected root fields", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
            },
          ],
          name: "unexpected",
        }),
      ),
    );

    expect(
      await screen.findByText("Unexpected field: name"),
    ).toBeInTheDocument();
  });

  it("rejects a case without a valid input", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "",
            },
          ],
        }),
      ),
    );

    expect(
      await screen.findByText("Case 1 must contain a non-empty input."),
    ).toBeInTheDocument();
  });

  it("rejects unexpected case fields", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
              unexpected: true,
            },
          ],
        }),
      ),
    );

    expect(
      await screen.findByText("Case 1 contains unexpected field: unexpected"),
    ).toBeInTheDocument();
  });

  it("rejects an invalid expected_output", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
              expected_output: 123,
            },
          ],
        }),
      ),
    );

    expect(
      await screen.findByText(
        "Case 1 expected_output must be a string or null.",
      ),
    ).toBeInTheDocument();
  });

  it("rejects invalid metadata", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
              metadata: [],
            },
          ],
        }),
      ),
    );

    expect(
      await screen.findByText("Case 1 metadata must be an object or null."),
    ).toBeInTheDocument();
  });

  it("accepts a valid JSON file and displays its name", async () => {
    const user = userEvent.setup();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
              expected_output: "Artificial Intelligence",
              metadata: {
                source: "test",
              },
            },
          ],
        }),
      ),
    );

    expect(
      await screen.findByText("Selected: dataset.json"),
    ).toBeInTheDocument();

    expect(screen.getByRole("button", { name: "Import JSON" })).toBeEnabled();
  });

  it("imports the parsed JSON payload", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockResolvedValue({
      id: "version-1",
      dataset_id: "dataset-1",
      version: 1,
      status: "ready",
      description: null,
      case_count: 1,
      is_active: true,
    });
    const onClose = vi.fn();

    mockedUseImportDataset.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={onClose}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    const payload = {
      cases: [
        {
          input: "What is AI?",
          expected_output: "Artificial Intelligence",
          metadata: {
            source: "test",
          },
        },
      ],
    };

    await user.upload(input, createJsonFile(JSON.stringify(payload)));

    await user.click(screen.getByRole("button", { name: "Import JSON" }));

    expect(mutateAsync).toHaveBeenCalledTimes(1);
    expect(mutateAsync).toHaveBeenCalledWith({
      datasetId: "dataset-1",
      payload,
    });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("displays an import error when the mutation fails", async () => {
    const user = userEvent.setup();
    const mutateAsync = vi.fn().mockRejectedValue(new Error("Import failed"));

    mockedUseImportDataset.mockReturnValue({
      mutateAsync,
      isPending: false,
    } as never);

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(
      input,
      createJsonFile(
        JSON.stringify({
          cases: [
            {
              input: "What is AI?",
            },
          ],
        }),
      ),
    );

    await user.click(screen.getByRole("button", { name: "Import JSON" }));

    expect(await screen.findByText("Import failed")).toBeInTheDocument();
  });

  it("disables actions while importing", () => {
    mockedUseImportDataset.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: true,
    } as never);

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={vi.fn()}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Select JSON File" }),
    ).toHaveAttribute("aria-disabled", "true");

    expect(screen.getByRole("button", { name: "Importing..." })).toBeDisabled();

    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("calls onClose when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <DatasetVersionImportDialog
        open
        datasetId="dataset-1"
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});



