import { Component, lazy, Suspense, type ErrorInfo, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { DatasetListPage } from "../features/datasets/DatasetListPage";
import { ModelListPage } from "../features/models/ModelListPage";
import { OrganizationListPage } from "../features/organizations/OrganizationListPage";
import { ProjectListPage } from "../features/projects/ProjectListPage";
import { DatasetVersionListPage } from "../features/datasetVersions/DatasetVersionListPage";
import { DatasetVersionDetailPage } from "../features/datasetVersions/DatasetVersionDetailPage";
import { DatasetCaseListPage } from "../features/datasetCases/DatasetCaseListPage";
import { EvaluationListPage } from "../features/evaluations/EvaluationListPage";
import { EvaluationViewPage } from "../features/evaluations/EvaluationViewPage";
import { CreateEvaluationPage } from "../features/evaluations/CreateEvaluationPage";
import { EvaluationSummaryPage } from "../features/evaluations/EvaluationSummaryPage";
import EvaluationResultsPage from "../features/evaluations/EvaluationResultsPage";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";

const ExperimentListPage = lazy(() =>
  import("../features/experiments/ExperimentListPage").then((module) => ({
    default: module.ExperimentListPage,
  })),
);
const ExperimentDetailPage = lazy(() =>
  import("../features/experiments/ExperimentDetailPage").then((module) => ({
    default: module.ExperimentDetailPage,
  })),
);

function ExperimentsRoute({ page }: { page: "list" | "detail" }) {
  const Page = page === "list" ? ExperimentListPage : ExperimentDetailPage;
  return (
    <ExperimentsErrorBoundary>
      <Suspense fallback={<LoadingState message="Loading experiments..." />}>
        <Page />
      </Suspense>
    </ExperimentsErrorBoundary>
  );
}

class ExperimentsErrorBoundary extends Component<
  { children: ReactNode },
  { errorMessage: string | null }
> {
  state: { errorMessage: string | null } = { errorMessage: null };

  static getDerivedStateFromError(error: unknown) {
    return {
      errorMessage: error instanceof Error ? error.message : String(error),
    };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    console.error("Experiments page failed to render.", error);
  }

  render() {
    if (this.state.errorMessage !== null) {
      return (
        <ErrorState
          title="Experiments page could not be displayed"
          message={`Experiments route error: ${this.state.errorMessage}`}
        />
      );
    }
    return this.props.children;
  }
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/organizations" element={<OrganizationListPage />} />
        <Route path="/projects" element={<ProjectListPage />} />
        <Route path="/datasets" element={<DatasetListPage />} />
        <Route
          path="/datasets/:datasetId/versions"
          element={<DatasetVersionListPage />}
        />
        <Route
          path="/datasets/:datasetId/versions/:versionId"
          element={<DatasetVersionDetailPage />}
        />
        <Route
          path="/datasets/:datasetId/versions/:versionId/cases"
          element={<DatasetCaseListPage />}
        />
        <Route path="/models" element={<ModelListPage />} />
        <Route path="/evaluations" element={<EvaluationListPage />} />
        <Route path="/evaluations/new" element={<CreateEvaluationPage />} />
        <Route
          path="/evaluations/:evaluationId/summary"
          element={<EvaluationSummaryPage />}
        />
        <Route
          path="/evaluations/:evaluationId/results"
          element={<EvaluationResultsPage />}
        />
        <Route
          path="/evaluations/:evaluationId"
          element={<EvaluationViewPage />}
        />
        <Route
          path="/experiments"
          element={<ExperimentsRoute page="list" />}
        />
        <Route
          path="/experiments/:experimentId"
          element={<ExperimentsRoute page="detail" />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
