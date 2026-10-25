import { createTheme, type PaletteMode } from "@mui/material/styles";

export function createAppTheme(mode: PaletteMode) {
  const dark = mode === "dark";
  const divider = dark ? "#334155" : "#e2e8f0";
  const tableBorder = dark ? "#334155" : "#f1f5f9";
  const fontFamily =
    'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';

  return createTheme({
    palette: {
      mode,
      primary: { main: dark ? "#818cf8" : "#4f46e5" },
      success: { main: dark ? "#4ade80" : "#15803d" },
      warning: { main: dark ? "#fbbf24" : "#b45309" },
      error: { main: dark ? "#f87171" : "#b91c1c" },
      info: { main: dark ? "#38bdf8" : "#0369a1" },
      background: {
        default: dark ? "#0f172a" : "#f8fafc",
        paper: dark ? "#1e293b" : "#ffffff",
      },
      text: {
        primary: dark ? "#f8fafc" : "#0f172a",
        secondary: dark ? "#d1d9e6" : "#64748b",
      },
      divider,
    },
    shape: { borderRadius: 10 },
    typography: {
      fontFamily,
      fontSize: 14,
      htmlFontSize: 16,
      allVariants: { fontFamily },
      h1: { fontSize: "2rem", fontWeight: 700, lineHeight: 1.2, letterSpacing: "-0.03em" },
      h2: { fontSize: "1.75rem", fontWeight: 700, lineHeight: 1.25, letterSpacing: "-0.025em" },
      h3: { fontSize: "1.5rem", fontWeight: 700, lineHeight: 1.3, letterSpacing: "-0.02em" },
      h4: {
        fontSize: "1.375rem",
        fontWeight: 700,
        lineHeight: 1.35,
        letterSpacing: "-0.015em",
      },
      h5: {
        fontSize: "1.25rem",
        fontWeight: 700,
        lineHeight: 1.4,
        letterSpacing: "-0.01em",
      },
      h6: {
        fontSize: "1.125rem",
        fontWeight: 700,
        lineHeight: 1.4,
      },
      subtitle1: { fontSize: "0.9375rem", fontWeight: 600, lineHeight: 1.5 },
      subtitle2: { fontSize: "0.875rem", fontWeight: 600, lineHeight: 1.45 },
      body1: { fontSize: "0.875rem", lineHeight: 1.6 },
      body2: { fontSize: "0.8125rem", lineHeight: 1.5 },
      button: { fontSize: "0.875rem", fontWeight: 600, textTransform: "none" },
      caption: { fontSize: "0.75rem", lineHeight: 1.45 },
      overline: { fontSize: "0.6875rem", fontWeight: 700, lineHeight: 1.5, letterSpacing: "0.06em" },
    },
    components: {
      MuiPaper: {
        styleOverrides: { root: { borderColor: divider } },
      },
      MuiDialog: {
        styleOverrides: {
          paper: { borderRadius: 12 },
        },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: { padding: "16px 24px", fontWeight: 700 },
        },
      },
      MuiDialogContent: {
        styleOverrides: {
          root: { padding: "16px 24px" },
          dividers: { paddingTop: 20, paddingBottom: 20 },
        },
      },
      MuiDialogActions: {
        styleOverrides: {
          root: { padding: "12px 24px 20px", gap: 8 },
          spacing: { "& > :not(style) ~ :not(style)": { marginLeft: 0 } },
        },
      },
      MuiCardContent: {
        styleOverrides: {
          root: { padding: 24, "&:last-child": { paddingBottom: 24 } },
        },
      },
      MuiTypography: {
        defaultProps: { variantMapping: { subtitle1: "p", subtitle2: "p" } },
      },
      MuiTableContainer: {
        styleOverrides: {
          root: {
            width: "100%",
            minWidth: 0,
            borderRadius: 10,
            maxHeight: "min(60vh, 560px)",
            overflowX: "auto",
            overflowY: "auto",
            overscrollBehavior: "contain",
            scrollbarWidth: "thin",
            scrollbarColor: `${dark ? "#64748b" : "#94a3b8"} transparent`,
            "&::-webkit-scrollbar": { width: 10, height: 10 },
            "&::-webkit-scrollbar-track": {
              backgroundColor: dark ? "#1e293b" : "#f1f5f9",
              borderRadius: 5,
            },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: dark ? "#64748b" : "#94a3b8",
              border: `2px solid ${dark ? "#1e293b" : "#f1f5f9"}`,
              borderRadius: 5,
            },
          },
        },
      },
      MuiTable: {
        styleOverrides: {
          root: {
            "& .MuiTableCell-head": {
              position: "sticky",
              top: 0,
              zIndex: 1,
              backgroundColor: dark ? "#1e293b" : "#ffffff",
              paddingTop: 14,
              paddingBottom: 14,
              color: dark ? "#cbd5e1" : "#64748b",
              fontSize: "0.8125rem",
              fontWeight: 600,
              lineHeight: 1.4,
              borderBottom: `1px solid ${divider}`,
              whiteSpace: "nowrap",
            },
            "& .MuiTableCell-body": {
              paddingTop: 16,
              paddingBottom: 16,
              borderBottom: `1px solid ${tableBorder}`,
            },
            "& .MuiTableRow-root:hover": {
              backgroundColor: dark ? "#263449" : "#f8fafc",
            },
            "& .MuiTableRow-root:last-child .MuiTableCell-body": {
              borderBottom: 0,
            },
          },
        },
      },
      MuiIconButton: { styleOverrides: { root: { borderRadius: 8 } } },
      MuiButton: {
        styleOverrides: {
          root: { borderRadius: 8, textTransform: "none", fontWeight: 600, fontFamily },
        },
      },
      MuiInputBase: {
        styleOverrides: { root: { fontFamily, fontSize: "0.875rem" } },
      },
      MuiFormLabel: {
        styleOverrides: { root: { fontFamily, fontSize: "0.875rem" } },
      },
      MuiChip: {
        styleOverrides: {
          root: { fontWeight: 600, borderRadius: 8 },
        },
      },
    },
  });
}
