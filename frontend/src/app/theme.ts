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
    },
    shape: {
        borderRadius: 10,
    },
});