import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DatasetVersionStatusChip } from "../../../features/datasetVersions/DatasetVersionStatusChip";

describe("DatasetVersionStatusChip", () => {
  it.each([
    ["draft", "Draft"],
    ["ready", "Ready"],
    ["archived", "Archived"],
  ] as const)("renders %s status as %s", (status, label) => {
    render(<DatasetVersionStatusChip status={status} />);

    expect(screen.getByText(label)).toBeInTheDocument();
  });
});
