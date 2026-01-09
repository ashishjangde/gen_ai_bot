"use client";

import React, { createContext, useContext } from "react";

interface ScrollContextType {
  scrollRef: React.RefObject<HTMLDivElement | null>;
}

const ScrollContext = createContext<ScrollContextType | undefined>(undefined);

export function useScrollContext() {
  const context = useContext(ScrollContext);
  if (!context) {
    throw new Error("useScrollContext must be used within a ScrollProvider");
  }
  return context;
}

export const ScrollProvider = ({
  children,
  scrollRef,
}: {
  children: React.ReactNode;
  scrollRef: React.RefObject<HTMLDivElement | null>;
}) => {
  return (
    <ScrollContext.Provider value={{ scrollRef }}>
      {children}
    </ScrollContext.Provider>
  );
};
