"use client";

/**
 * Application-wide providers for TechPulse.
 *
 * Wraps the component tree with necessary context providers including
 * TanStack Query for server state management.
 *
 * @module components/providers
 */

import { useState, type ReactNode } from "react";

import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { getQueryClient } from "@/lib/api/query-client";

/**
 * Props for the Providers component.
 */
export interface ProvidersProps {
  /** Child components to wrap with providers. */
  readonly children: ReactNode;
}

/**
 * Root providers wrapper for the application.
 *
 * Configures:
 * - TanStack Query with optimized defaults for analytical data
 * - DevTools panel in development mode only
 *
 * Must be used as a Client Component due to QueryClientProvider requirements.
 * Place in root layout to enable data fetching throughout the app.
 *
 * @param props - Component props.
 * @param props.children - Child components to render within providers.
 *
 * @example
 * ```tsx
 * // In app/layout.tsx
 * export default function RootLayout({ children }: { children: ReactNode }) {
 *   return (
 *     <html>
 *       <body>
 *         <Providers>{children}</Providers>
 *       </body>
 *     </html>
 *   );
 * }
 * ```
 */
export function Providers({ children }: ProvidersProps): ReactNode {
  // Create QueryClient in state to ensure it's created once per component instance
  // This pattern is recommended by TanStack Query for Next.js App Router
  const [queryClient] = useState(() => getQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-left"
        />
      )}
    </QueryClientProvider>
  );
}
