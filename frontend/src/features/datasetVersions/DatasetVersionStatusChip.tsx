import { StatusChip } from "../../components/common/StatusChip";
import type { DatasetVersionStatus } from "./api";

export function DatasetVersionStatusChip({
  status,
}: {
  status: DatasetVersionStatus;
}) {
  return <StatusChip status={status} />;
}
