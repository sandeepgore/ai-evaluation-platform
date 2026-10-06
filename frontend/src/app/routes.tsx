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

function PlaceholderPage({ title }: { title: string }) {
  return <h1>{title}</h1>;
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
        <Route
          path="/evaluations/:evaluationId"
          element={<EvaluationViewPage />}
        />
        <Route
          path="/experiments"
          element={<PlaceholderPage title="Experiments" />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
