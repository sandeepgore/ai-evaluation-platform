import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";

function PlaceholderPage({ title }: { title: string }) {
  return <h1>{title}</h1>;
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="/"
          element={<PlaceholderPage title="Dashboard" />}
        />
        <Route
          path="/organizations"
          element={<PlaceholderPage title="Organizations" />}
        />
        <Route
          path="/projects"
          element={<PlaceholderPage title="Projects" />}
        />
        <Route
          path="/datasets"
          element={<PlaceholderPage title="Datasets" />}
        />
        <Route
          path="/models"
          element={<PlaceholderPage title="Models" />}
        />
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