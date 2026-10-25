import { Component, lazy, Suspense, type ErrorInfo, type ReactNode } from "react";
import { Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";
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
import { LoginPage } from "../features/auth/LoginPage";
import { UserAccessPage } from "../features/auth/UserAccessPage";
import { AuditLogsPage } from "../features/auditLogs/AuditLogsPage";
import { useAuthStore } from "../store/authStore";

function RequireAuth() {
  const token = useAuthStore((state) => state.token);
  const location = useLocation();
  return token ? <Outlet /> : <Navigate to="/login" replace state={{ from: location.pathname }} />;
}

function RequireAdmin() {
  const role = useAuthStore((state) => state.user?.role);
  return role === "admin" ? <Outlet /> : <Navigate to="/" replace />;
}

function RequireWriteAccess() {
  const role = useAuthStore((state) => state.user?.role);
  return role === "admin" || role === "dev" ? <Outlet /> : <Navigate to="/" replace />;
}

function AuthenticatedShell() {
  return <AppShell />;
}

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
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth />}>
      <Route element={<AuthenticatedShell />}>
        <Route element={<RequireAdmin />}>
        <Route path="/admin/users" element={<UserAccessPage />} />
        <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
        </Route>
        <Route element={<RequireWriteAccess />}>
          <Route path="/evaluations/new" element={<CreateEvaluationPage />} />
        </Route>
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
      </Route>
    </Routes>
  );
}
