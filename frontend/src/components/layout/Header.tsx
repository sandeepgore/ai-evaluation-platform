import { AccountCircleOutlined, MenuOutlined } from "@mui/icons-material";
import {
  AppBar,
  Box,
  Divider,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";
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
      <Toolbar
        sx={{
          minHeight: 64,
          px: { xs: 2, md: 3 },
          gap: 2,
        }}
      >
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
            fontWeight: 700,
            letterSpacing: "-0.015em",
            color: "text.primary",
            flexShrink: 0,
          }}
        >
          {title}
        </Typography>

        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            display: { xs: "none", sm: "flex" },
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 1,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: "text.secondary",
              fontWeight: 500,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: { sm: 180, md: 240 },
            }}
          >
            {selectedOrganization?.name ?? "No organization"}
          </Typography>

          <Typography
            component="span"
            aria-hidden="true"
            sx={{
              color: "text.disabled",
              fontSize: 18,
              lineHeight: 1,
            }}
          >
            ›
          </Typography>

          <Typography
            variant="body2"
            sx={{
              color: "text.primary",
              fontWeight: 600,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: { sm: 200, md: 280 },
            }}
          >
            {selectedProject?.name ?? "No project"}
          </Typography>
        </Box>

        <Divider
          orientation="vertical"
          flexItem
          sx={{
            display: { xs: "none", sm: "block" },
            my: 1.5,
          }}
        />

        <IconButton
          aria-label="account"
          sx={{
            color: "text.secondary",
          }}
        >
          <AccountCircleOutlined />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}
