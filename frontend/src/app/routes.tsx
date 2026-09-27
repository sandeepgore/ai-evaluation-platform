import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { ModelListPage } from "../features/models/ModelListPage";
import { OrganizationListPage } from "../features/organizations/OrganizationListPage";
import { ProjectListPage } from "../features/projects/ProjectListPage";

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
        <Route
          path="/datasets"
          element={<PlaceholderPage title="Datasets" />}
        />
        <Route path="/models" element={<ModelListPage />} />
        <Route
          path="/evaluations"
          element={<PlaceholderPage title="Evaluations" />}
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
