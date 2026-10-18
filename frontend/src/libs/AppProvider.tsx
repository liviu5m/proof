import React, { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { User } from "@/types";
import { getUserJwt } from "@/api/user";
import FullScreenLoader from "@/components/FullLoader";

interface AppContextType {
  user: User | null;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const { data: user, isPending } = useQuery({
    queryKey: ["jwt-user"],
    queryFn: () => getUserJwt(),
    retry: false,
  });

  return isPending ? (
    <FullScreenLoader />
  ) : (
    <AppContext.Provider
      value={{
        user,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};
