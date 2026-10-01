import axios from "axios";

const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
    headers: {
        "Content-Type": "application/json",
    },
});

apiClient.interceptors.response.use(
    (response) => response,
    (error: unknown) => {
        if (axios.isAxiosError(error)) {
            const detail = error.response?.data?.detail;

            if (typeof detail === "string") {
                return Promise.reject(new Error(detail));
            }
        }

        return Promise.reject(error);
    },
);

export { apiClient };