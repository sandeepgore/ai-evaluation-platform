const evaluationStatusPollIntervalMs = Number(
    import.meta.env.VITE_EVALUATION_STATUS_POLL_INTERVAL_MS ?? 30000,
);

export const config = {
    apiUrl: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
    evaluation: {
        statusPollIntervalMs: evaluationStatusPollIntervalMs,
    },
} as const;