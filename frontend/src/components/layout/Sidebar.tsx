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
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          AI Evaluation
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Platform
        </Typography>
      </Box>

      <Divider />

      <List sx={{ px: 1, py: 1 }}>
        {navigationItems.map((item) => (
          <ListItemButton
            key={item.path}
            component={NavLink}
            to={item.path}
            end={item.path === "/"}
            sx={{
              borderRadius: 1.5,
              mb: 0.5,
              "&.active": {
                bgcolor: "primary.main",
                color: "primary.contrastText",
                "& .MuiListItemIcon-root": {
                  color: "inherit",
                },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>

            <ListItemText primary={item.label} />
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
          },
        }}
      >
        <SidebarContent />
      </Drawer>
    </>
  );
}
