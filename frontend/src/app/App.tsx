import { useCallback, useMemo, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { CssBaseline, ThemeProvider } from "@mui/material";
import type { PaletteMode } from "@mui/material/styles";
import { BrowserRouter } from "react-router-dom";
import { createAppTheme } from "./theme";
import { ColorModeContext } from "./ColorModeContext";
import { AppRoutes } from "./routes";
import { NotificationProvider } from "../components/common/NotificationProvider";

const queryClient = new QueryClient();

export function App() {
  const [mode, setMode] = useState<PaletteMode>(() =>
    window.localStorage.getItem("ai-evaluation-color-mode") === "light"
      ? "light"
      : "dark",
  );
  const toggleColorMode = useCallback(() => {
    setMode((currentMode) => {
      const nextMode = currentMode === "light" ? "dark" : "light";
      window.localStorage.setItem("ai-evaluation-color-mode", nextMode);
      return nextMode;
    });
  }, []);
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <ColorModeContext.Provider value={{ mode, toggleColorMode }}>
          <CssBaseline />
          <BrowserRouter>
            <NotificationProvider>
              <AppRoutes />
            </NotificationProvider>
          </BrowserRouter>
        </ColorModeContext.Provider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
