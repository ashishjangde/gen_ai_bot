"use client";

import { motion } from "motion/react";
import { 
  Brain, 
  Code, 
  Search, 
  Zap, 
  Share2, 
  ShieldCheck,
  ArrowUpRight 
} from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    title: "Second Brain",
    description: "Store, organize, and recall any piece of information instantly. Your digital memory, upgraded.",
    icon: <Brain className="h-6 w-6 text-pink-400" />,
    className: "md:col-span-2",
  },
  {
    title: "Deep Search",
    description: "Search across your files, apps, and the web simultaneously.",
    icon: <Search className="h-6 w-6 text-blue-400" />,
    className: "md:col-span-1",
  },
  {
    title: "Code Intelligence",
    description: "Generate, debug, and explain code in any language with context-aware AI.",
    icon: <Code className="h-6 w-6 text-green-400" />,
    className: "md:col-span-1",
  },
  {
    title: "Instant Sync",
    description: "Real-time synchronization across all your devices.",
    icon: <Zap className="h-6 w-6 text-yellow-400" />,
    className: "md:col-span-2",
  },
  {
    title: "Secure by Design",
    description: "Enterprise-grade encryption for all your personal data.",
    icon: <ShieldCheck className="h-6 w-6 text-purple-400" />,
    className: "md:col-span-3",
  },
];

const BentoCard = ({ 
  title, 
  description, 
  icon, 
  className 
}: { 
  title: string; 
  description: string; 
  icon: React.ReactNode; 
  className?: string; 
}) => {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className={cn(
        "group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-md transition-all hover:bg-white/10 hover:shadow-2xl hover:shadow-primary/10",
        className
      )}
    >
      <div className="absolute -right-10 -top-10 h-64 w-64 rounded-full bg-primary/20 blur-[100px] transition-all group-hover:bg-primary/30" />
      
      <div className="relative z-10 mb-4 flex items-center justify-between">
        <div className="rounded-xl bg-white/10 p-3 ring-1 ring-white/20 transition-all group-hover:bg-white/20">
          {icon}
        </div>
        <ArrowUpRight className="h-5 w-5 text-gray-500 opacity-0 transition-all group-hover:opacity-100 group-hover:text-white" />
      </div>
      
      <div className="relative z-10">
        <h3 className="mb-2 text-xl font-bold text-white tracking-tight">{title}</h3>
        <p className="text-sm text-gray-400 leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
};

export function BentoGridSection() {
  return (
    <section className="relative w-full py-24 bg-gray-950 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full max-w-7xl opacity-20 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-[128px]" />
      </div>

      <div className="container relative z-10 mx-auto px-4">
        <div className="mb-16 text-center">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl font-bold tracking-tighter text-white sm:text-5xl"
          >
            Built for your <span className="text-primary">Second Brain</span>
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="mt-4 text-gray-400"
          >
             Experience the power of a fully integrated digital workspace.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 max-w-5xl mx-auto">
          {features.map((feature, idx) => (
            <BentoCard
              key={idx}
              title={feature.title}
              description={feature.description}
              icon={feature.icon}
              className={feature.className}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
