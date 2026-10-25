import axios from "axios";
import { useAuthStore } from "../../store/authStore";

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
    headers: {
        "Content-Type": "application/json",
    },
});

apiClient.interceptors.request.use((config) => {
    const token = useAuthStore.getState().token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 401) useAuthStore.getState().clearSession();
            const detail = error.response?.data?.detail;

            if (typeof detail === "string") {
                return Promise.reject(new Error(detail));
            }
        }

        return Promise.reject(error);
    },
);

export { apiClient };
