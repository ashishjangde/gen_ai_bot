"use client";

import { motion } from "motion/react";
import { IconBrandTwitter, IconBrandGithub, IconBrandLinkedin, IconBrandDiscord } from "@tabler/icons-react";
import { cn } from "@/lib/utils";

const footerLinks = [
  {
    title: "Product",
    links: [
      { name: "Features", href: "#" },
      { name: "Pricing", href: "#" },
      { name: "Integrations", href: "#" },
      { name: "Changelog", href: "#" },
    ],
  },
  {
    title: "Resources",
    links: [
      { name: "Documentation", href: "#" },
      { name: "API Reference", href: "#" },
      { name: "Blog", href: "#" },
      { name: "Community", href: "#" },
    ],
  },
  {
    title: "Company",
    links: [
      { name: "About", href: "#" },
      { name: "Careers", href: "#" },
      { name: "Legal", href: "#" },
      { name: "Contact", href: "#" },
    ],
  },
];

const socialLinks = [
  { icon: IconBrandTwitter, href: "#", label: "Twitter" },
  { icon: IconBrandGithub, href: "#", label: "GitHub" },
  { icon: IconBrandLinkedin, href: "#", label: "LinkedIn" },
  { icon: IconBrandDiscord, href: "#", label: "Discord" },
];

export function Footer() {
  return (
    <footer className="relative w-full overflow-hidden bg-background pt-20 pb-10">
      {/* Gradient Top Border */}
      <div className="absolute top-0 left-0 h-px w-full bg-linear-to-r from-transparent via-primary/50 to-transparent" />
      
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 h-64 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[100px]" />

      <div className="container relative z-10 mx-auto px-4 md:px-6">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-2 lg:grid-cols-5 lg:gap-8">
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-2">
              <img src="/logo.svg" alt="GroqChat Logo" className="h-8 w-8" />
              <span className="text-xl font-bold bg-clip-text text-transparent bg-linear-to-br from-foreground to-muted-foreground">
                GroqChat
              </span>
            </div>
            <p className="mt-4 max-w-xs text-sm text-muted-foreground">
              Empowering the next generation of AI applications with lightning-fast inference and futuristic design.
            </p>
            <div className="mt-6 flex space-x-4">
              {socialLinks.map((social, idx) => (
                <motion.a
                  key={idx}
                  href={social.href}
                  whileHover={{ y: -3, scale: 1.1 }}
                  className="rounded-full bg-accent/50 p-2 text-muted-foreground transition-colors hover:bg-primary/20 hover:text-primary"
                  aria-label={social.label}
                >
                  <social.icon size={20} />
                </motion.a>
              ))}
            </div>
          </div>

          {/* Links Columns */}
          {footerLinks.map((column, idx) => (
            <div key={idx} className="flex flex-col space-y-4">
              <h3 className="text-sm font-semibold tracking-wider text-foreground uppercase">
                {column.title}
              </h3>
              <ul className="space-y-3 text-sm">
                {column.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    <a
                      href={link.href}
                      className="text-muted-foreground transition-all hover:text-primary hover:pl-1"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <div className="mt-16 flex flex-col items-center justify-between border-t border-border/40 pt-8 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} GroqChat Inc. All rights reserved.
          </p>
          <div className="mt-4 flex space-x-6 sm:mt-0">
             <a href="#" className="text-xs text-muted-foreground hover:text-foreground">Privacy Policy</a>
             <a href="#" className="text-xs text-muted-foreground hover:text-foreground">Terms of Service</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
