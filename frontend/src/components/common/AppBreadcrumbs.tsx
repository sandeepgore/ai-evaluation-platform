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
  return (
    <Breadcrumbs
      aria-label="breadcrumb"
      sx={{
        "& .MuiBreadcrumbs-separator": {
          color: "text.disabled",
        },
      }}
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1;

        if (isLast || !item.to) {
          return (
            <Typography
              key={`${item.label}-${index}`}
              variant="body2"
              color={isLast ? "text.primary" : "text.secondary"}
              sx={{
                fontWeight: isLast ? 600 : 500,
              }}
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
