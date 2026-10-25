import {
  AccountCircleOutlined,
  DarkModeOutlined,
  LightModeOutlined,
  LogoutOutlined,
  ManageAccountsOutlined,
  MenuOutlined,
} from "@mui/icons-material";
import { useContext, useState } from "react";
import {
  AppBar,
  Box,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { Link, useLocation } from "react-router-dom";
import { useOrganizations } from "../../features/organizations/hooks";
import { useProjects } from "../../features/projects/hooks";
import { useAppContextStore } from "../../store/appContextStore";
import { useAuthStore } from "../../store/authStore";
import { ColorModeContext } from "../../app/ColorModeContext";

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
  const { mode, toggleColorMode } = useContext(ColorModeContext);
  const [accountAnchor, setAccountAnchor] = useState<HTMLElement | null>(null);
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);
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
  const accountName = user?.full_name || user?.email || "Account";
  const closeAccountMenu = () => setAccountAnchor(null);

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
          title="Open navigation"
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

        <Tooltip title={`Switch to ${mode === "light" ? "dark" : "light"} mode`}>
          <IconButton
            aria-label={`Switch to ${mode === "light" ? "dark" : "light"} mode`}
            onClick={toggleColorMode}
            color="inherit"
          >
            {mode === "light" ? <DarkModeOutlined /> : <LightModeOutlined />}
          </IconButton>
        </Tooltip>
        <Tooltip title="Account menu">
          <IconButton
            aria-label="Open account menu"
            aria-haspopup="true"
            aria-expanded={Boolean(accountAnchor)}
            onClick={(event) => setAccountAnchor(event.currentTarget)}
            color="inherit"
          >
            <AccountCircleOutlined />
          </IconButton>
        </Tooltip>
        <Menu
          anchorEl={accountAnchor}
          open={Boolean(accountAnchor)}
          onClose={closeAccountMenu}
          anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
          transformOrigin={{ vertical: "top", horizontal: "right" }}
          slotProps={{ paper: { sx: { minWidth: 220, mt: 1 } } }}
        >
          <Box sx={{ px: 2, py: 1.25 }}>
            <Typography variant="body2" fontWeight={700} noWrap>
              {accountName}
            </Typography>
            {user?.full_name && (
              <Typography variant="caption" color="text.secondary" noWrap display="block">
                {user.email}
              </Typography>
            )}
            {user?.role && (
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "capitalize" }}>
                {user.role}
              </Typography>
            )}
          </Box>
          <Divider />
          {user?.role === "admin" && (
            <MenuItem component={Link} to="/admin/users" onClick={closeAccountMenu}>
              <ListItemIcon><ManageAccountsOutlined fontSize="small" /></ListItemIcon>
              <ListItemText>User access</ListItemText>
            </MenuItem>
          )}
          {user?.role === "admin" && <Divider />}
          <MenuItem onClick={() => { closeAccountMenu(); clearSession(); }}>
            <ListItemIcon><LogoutOutlined fontSize="small" /></ListItemIcon>
            <ListItemText>Sign out</ListItemText>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
