import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  NotificationSnackbar,
  type NotificationSeverity,
} from "./NotificationSnackbar";

interface NotificationContextValue {
  notify: (message: string, severity?: NotificationSeverity) => void;
}

const NotificationContext = createContext<NotificationContextValue | null>(
  null,
);

interface NotificationState {
  message: string;
  severity: NotificationSeverity;
}

interface NotificationProviderProps {
  children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
  const [notification, setNotification] = useState<NotificationState | null>(
    null,
  );

  const notify = useCallback(
    (message: string, severity: NotificationSeverity = "info") => {
      setNotification({
        message,
        severity,
      });
    },
    [],
  );

  const handleClose = useCallback(() => {
    setNotification(null);
  }, []);

  const value = useMemo(
    () => ({
      notify,
    }),
    [notify],
  );

  return (
    <NotificationContext.Provider value={value}>
      {children}

      {notification && (
        <NotificationSnackbar
          open
          message={notification.message}
          severity={notification.severity}
          onClose={handleClose}
        />
      )}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);

  if (!context) {
    throw new Error(
      "useNotification must be used within NotificationProvider.",
    );
  }

  return context;
}
