import {
  RenderOptions,
  render as rtlRender,
  screen as rtlScreen,
  fireEvent as rtlFireEvent,
  waitFor as rtlWaitFor,
  act as rtlAct,
} from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React, { ReactNode } from "react";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

export const render = (
  ui: ReactNode,
  options?: Omit<RenderOptions, "wrapper">
) => {
  return rtlRender(ui, { wrapper: Wrapper, ...options });
};

export const screen = rtlScreen;
export const fireEvent = rtlFireEvent;
export const waitFor = rtlWaitFor;
export const act = rtlAct;