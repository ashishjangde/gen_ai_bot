import { Footer } from "./_components/base/footer";
import { NavbarWrapper } from "./_components/base/navbar-wrapper";


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="relative w-full">
      <NavbarWrapper />
      {children}
      <Footer />
    </div>
  );
}
