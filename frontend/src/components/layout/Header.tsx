import {
  AccountCircleOutlined,
  MenuOutlined,
} from "@mui/icons-material";
import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";
import { useLocation } from "react-router-dom";

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

        <Box>
          <IconButton aria-label="account">
            <AccountCircleOutlined />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}