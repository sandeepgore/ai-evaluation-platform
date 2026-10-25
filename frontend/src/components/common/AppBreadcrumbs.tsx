import {
  Breadcrumbs,
  Link,
  Typography,
} from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface AppBreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function AppBreadcrumbs({ items }: AppBreadcrumbsProps) {
  const ancestors = items.slice(0, -1);
  if (ancestors.length === 0) return null;

  return (
    <Breadcrumbs
      aria-label="breadcrumb"
      sx={{
        "& .MuiBreadcrumbs-separator": {
          color: "text.disabled",
        },
      }}
    >
      {ancestors.map((item, index) => {
        if (!item.to) {
          return (
            <Typography
              key={`${item.label}-${index}`}
              variant="body2"
              color="text.secondary"
              sx={{ fontWeight: 500 }}
            >
              {item.label}
            </Typography>
          );
        }

        return (
          <Link
            key={`${item.label}-${index}`}
            component={RouterLink}
            to={item.to}
            underline="hover"
            color="text.secondary"
            variant="body2"
            sx={{
              fontWeight: 500,
            }}
          >
            {item.label}
          </Link>
        );
      })}
    </Breadcrumbs>
  );
}
