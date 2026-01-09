import { ThemeProvider } from "./theme-provider";

export default function GlobalProviders({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
    <ThemeProvider attribute="class">
      {children}
    </ThemeProvider>
    </>
  )
}
