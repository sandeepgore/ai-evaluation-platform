import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
    palette: {
        mode: "light",

        primary: {
            main: "#4f46e5",
        },

        background: {
            default: "#f8fafc",
            paper: "#ffffff",
        },

        text: {
            primary: "#0f172a",
            secondary: "#64748b",
        },

        divider: "#e2e8f0",
    },

    shape: {
        borderRadius: 10,
    },

    typography: {
        fontFamily:
            'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',

        h4: {
            fontSize: "1.75rem",
            fontWeight: 700,
            lineHeight: 1.25,
            letterSpacing: "-0.025em",
        },

        h5: {
            fontSize: "1.5rem",
            fontWeight: 700,
            lineHeight: 1.3,
            letterSpacing: "-0.02em",
        },

        h6: {
            fontSize: "1.125rem",
            fontWeight: 650,
            lineHeight: 1.4,
            letterSpacing: "-0.01em",
        },

        body1: {
            fontSize: "0.9375rem",
            lineHeight: 1.6,
        },

        body2: {
            fontSize: "0.875rem",
            lineHeight: 1.5,
        },
    },

    components: {
        MuiPaper: {
            styleOverrides: {
                root: {
                    borderColor: "#e2e8f0",
                },
            },
        },

        MuiTableContainer: {
            styleOverrides: {
                root: {
                    borderRadius: 10,
                    overflow: "hidden",
                },
            },
        },

        MuiTable: {
            styleOverrides: {
                root: {
                    "& .MuiTableCell-head": {
                        paddingTop: 14,
                        paddingBottom: 14,
                        color: "#64748b",
                        fontSize: "0.8125rem",
                        fontWeight: 600,
                        lineHeight: 1.4,
                        borderBottom: "1px solid #e2e8f0",
                        whiteSpace: "nowrap",
                    },

                    "& .MuiTableCell-body": {
                        paddingTop: 16,
                        paddingBottom: 16,
                        borderBottom: "1px solid #f1f5f9",
                    },

                    "& .MuiTableRow-root:hover": {
                        backgroundColor: "#f8fafc",
                    },

                    "& .MuiTableRow-root:last-child .MuiTableCell-body": {
                        borderBottom: 0,
                    },
                },
            },
        },

        MuiIconButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                },
            },
        },

        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    textTransform: "none",
                    fontWeight: 600,
                },
            },
        },

        MuiChip: {
            styleOverrides: {
                root: {
                    fontWeight: 600,
                    borderRadius: 8,
                },
            },
        },
    },
});