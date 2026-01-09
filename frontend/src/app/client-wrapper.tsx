"use client";

import GlobalProviders from "@/components/providers";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ScrollProvider } from "@/components/providers/scroll-provider";
import { useRef, useEffect } from "react";
import Lenis from "lenis";

export default function ClientWrapper({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const viewportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scrollContainer = viewportRef.current;
    if (!scrollContainer) return;

    const lenis = new Lenis({
      wrapper: scrollContainer,
      content: scrollContainer.firstChild as HTMLElement,
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    });

    function raf(time: number) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);

    return () => {
      lenis.destroy();
    };
  }, []);

  return (
    <GlobalProviders>
      <ScrollProvider scrollRef={viewportRef}>
        <ScrollArea viewportRef={viewportRef} className="h-screen w-full">
          {children}
        </ScrollArea>
      </ScrollProvider>
    </GlobalProviders>
  );
}
