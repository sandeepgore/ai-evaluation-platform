import { AccountCircleOutlined, MenuOutlined } from "@mui/icons-material";
import { AppBar, Box, IconButton, Toolbar, Typography } from "@mui/material";
import { useLocation } from "react-router-dom";
import { useOrganizations } from "../../features/organizations/hooks";
import { useProjects } from "../../features/projects/hooks";
import { useAppContextStore } from "../../store/appContextStore";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/organizations": "Organizations",
  "/projects": "Projects",
  "/datasets": "Datasets",
  "/models": "Models",
  "/evaluations": "Evaluations",
  "/experiments": "Experiments",
};

interface HeaderProps {
  onMenuClick: () => void;
}

export function Header({ onMenuClick }: HeaderProps) {
  const location = useLocation();
  const title = pageTitles[location.pathname] ?? "AI Evaluation Platform";

  const { data: organizations = [] } = useOrganizations();

  const selectedOrganizationId = useAppContextStore(
    (state) => state.selectedOrganizationId,
  );
  const selectedProjectId = useAppContextStore(
    (state) => state.selectedProjectId,
  );

  const { data: projects = [] } = useProjects(selectedOrganizationId);

  const selectedOrganization = organizations.find(
    (organization) => organization.id === selectedOrganizationId,
  );

  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId,
  );

  return (
    <AppBar
      position="sticky"
      color="inherit"
      elevation={0}
      sx={{
        borderBottom: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
      }}
    >
      <Toolbar sx={{ gap: 1 }}>
        <IconButton
          aria-label="open navigation"
          onClick={onMenuClick}
          sx={{
            display: { xs: "inline-flex", lg: "none" },
          }}
        >
          <MenuOutlined />
        </IconButton>

        <Typography
          variant="h6"
          sx={{
            fontWeight: 600,
            flex: 1,
          }}
        >
          {title}
        </Typography>

        <Box
          sx={{
            display: { xs: "none", sm: "block" },
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Organization:{" "}
            <Typography
              component="span"
              variant="body2"
              color="text.primary"
              sx={{ fontWeight: 600 }}
            >
              {selectedOrganization?.name ?? "None"}
            </Typography>
            {" | "}
            Project:{" "}
            <Typography
              component="span"
              variant="body2"
              color="text.primary"
              sx={{ fontWeight: 600 }}
            >
              {selectedProject?.name ?? "None"}
            </Typography>
          </Typography>
        </Box>

        <Box>
          <IconButton aria-label="account">
            <AccountCircleOutlined />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
