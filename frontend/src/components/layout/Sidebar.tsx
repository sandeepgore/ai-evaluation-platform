import {
  AssessmentOutlined,
  BusinessOutlined,
  DashboardOutlined,
  DatasetOutlined,
  FolderOutlined,
  ModelTrainingOutlined,
  ScienceOutlined,
} from "@mui/icons-material";
import {
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import { NavLink } from "react-router-dom";

const drawerWidth = 240;

const navigationItems = [
  {
    label: "Dashboard",
    path: "/",
    icon: <DashboardOutlined />,
  },
  {
    label: "Organizations",
    path: "/organizations",
    icon: <BusinessOutlined />,
  },
  {
    label: "Projects",
    path: "/projects",
    icon: <FolderOutlined />,
  },
  {
    label: "Datasets",
    path: "/datasets",
    icon: <DatasetOutlined />,
  },
  {
    label: "Models",
    path: "/models",
    icon: <ModelTrainingOutlined />,
  },
  {
    label: "Evaluations",
    path: "/evaluations",
    icon: <AssessmentOutlined />,
  },
  {
    label: "Experiments",
    path: "/experiments",
    icon: <ScienceOutlined />,
  },
];

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

function SidebarContent() {
  return (
    <Box
      sx={{
        width: drawerWidth,
        height: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ px: 2.5, py: 2.5 }}>
        <Typography
          variant="h6"
          sx={{
            fontWeight: 700,
            letterSpacing: "-0.02em",
            color: "text.primary",
          }}
        >
          AI Evaluation
        </Typography>

        <Typography
          variant="body2"
          sx={{
            color: "text.secondary",
            mt: 0.25,
          }}
        >
          Platform
        </Typography>
      </Box>

      <Divider />

      <List
        sx={{
          px: 1.25,
          py: 1.5,
        }}
      >
        {navigationItems.map((item) => (
          <ListItemButton
            key={item.path}
            component={NavLink}
            to={item.path}
            end={item.path === "/"}
            sx={{
              minHeight: 44,
              borderRadius: 2,
              mb: 0.5,
              px: 1.5,
              color: "text.secondary",
              transition: "background-color 120ms ease, color 120ms ease",

              "&:hover": {
                bgcolor: "action.hover",
                color: "text.primary",
              },

              "&.active": {
                bgcolor: "primary.50",
                color: "primary.main",
                fontWeight: 600,

                "& .MuiListItemIcon-root": {
                  color: "primary.main",
                },

                "&:hover": {
                  bgcolor: "primary.100",
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                minWidth: 40,
                color: "inherit",
              }}
            >
              {item.icon}
            </ListItemIcon>

            <ListItemText
              primary={
                <Typography
                  component="span"
                  sx={{
                    fontSize: 14,
                    fontWeight: "inherit",
                  }}
                >
                  {item.label}
                </Typography>
              }
            />
          </ListItemButton>
        ))}
      </List>
    </Box>
  );
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  return (
    <>
      <Box
        component="aside"
        sx={{
          display: { xs: "none", lg: "block" },
          width: drawerWidth,
          flexShrink: 0,
        }}
      >
        <Box
          sx={{
            position: "fixed",
            width: drawerWidth,
            height: "100vh",
            borderRight: 1,
            borderColor: "divider",
            bgcolor: "background.paper",
            boxShadow: "1px 0 3px rgba(15, 23, 42, 0.04)",
          }}
        >
          <SidebarContent />
        </Box>
      </Box>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: "block", lg: "none" },
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            bgcolor: "background.paper",
          },
        }}
      >
        <SidebarContent />
      </Drawer>
    </>
  );
}
