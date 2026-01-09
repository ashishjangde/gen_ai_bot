"use client";

import { motion } from "motion/react";
import { FileText, Github, Slack, Globe, Database, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";

export function FeatureHighlight() {
  const apps = [
    { icon: <Github className="h-6 w-6" />, label: "GitHub", color: "bg-gray-800" },
    { icon: <Slack className="h-6 w-6" />, label: "Slack", color: "bg-red-500" },
    { icon: <Globe className="h-6 w-6" />, label: "Web", color: "bg-blue-500" },
    { icon: <Database className="h-6 w-6" />, label: "Drive", color: "bg-green-500" },
    { icon: <FileText className="h-6 w-6" />, label: "Notion", color: "bg-black" },
    { icon: <MessageSquare className="h-6 w-6" />, label: "Discord", color: "bg-indigo-500" },
  ];

  return (
    <section className="relative w-full py-24 bg-gray-950 overflow-hidden border-t border-white/5">
      <div className="container px-4 mx-auto">
        <div className="grid gap-16 lg:grid-cols-2 items-center">
          
          {/* Left: Text Content */}
          <div className="flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="inline-flex items-center rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-sm font-medium text-primary w-fit"
            >
              <span>Universal Connectivity</span>
            </motion.div>
            
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-3xl font-bold tracking-tighter text-white sm:text-4xl md:text-5xl"
            >
              Connect your entire <br />
              <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-400 to-purple-400">
                digital ecosystem.
              </span>
            </motion.h2>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="text-lg text-gray-400 leading-relaxed max-w-lg"
            >
              Stop switching tabs. Our AI connects directly to your documents, repositories, and chat history. Ask questions across all your data in one place.
            </motion.p>

            <motion.div
               initial={{ opacity: 0, y: 20 }}
               whileInView={{ opacity: 1, y: 0 }}
               viewport={{ once: true }}
               transition={{ delay: 0.2 }}
            >
                <button className="rounded-full bg-white px-8 py-3 font-semibold text-black transition-transform hover:scale-105 active:scale-95">
                    Start Integrating
                </button>
            </motion.div>
          </div>

          {/* Right: Visual Graphic (The "Brain" Effect) */}
          <div className="relative flex items-center justify-center min-h-[400px]">
             {/* Central Core */}
             <div className="relative z-10 flex h-32 w-32 items-center justify-center rounded-full border border-white/20 bg-black/50 backdrop-blur-xl shadow-[0_0_50px_rgba(59,130,246,0.2)]">
                <div className="absolute inset-0 rounded-full border border-primary/50 opacity-50 animate-[spin_10s_linear_infinite]" />
                <div className="h-4 w-4 rounded-full bg-primary shadow-[0_0_20px_rgba(59,130,246,1)]" />
             </div>

             {/* Orbiting Apps */}
             {apps.map((app, i) => {
                const angle = (i * 360) / apps.length;
                const radius = 160; // Distance from center
                const x = Math.cos((angle * Math.PI) / 180) * radius;
                const y = Math.sin((angle * Math.PI) / 180) * radius;
                
                return (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    style={{ 
                        position: 'absolute',
                        left: `calc(50% + ${x}px)`,
                        top: `calc(50% + ${y}px)`,
                        transform: 'translate(-50%, -50%)'
                    }}
                    className="flex flex-col items-center gap-2"
                  >
                    <div className={cn("flex h-12 w-12 items-center justify-center rounded-2xl border border-white/10 text-white shadow-lg backdrop-blur-md transition-all hover:scale-110 hover:border-white/30", app.color)}>
                        {app.icon}
                    </div>
                    {/* Connecting Line (Pseudo-visual) */}
                    <div 
                        className="absolute top-1/2 left-1/2 -z-10 h-px bg-linear-to-r from-transparent via-white/20 to-transparent w-[160px] origin-left"
                        style={{
                           width: `${radius}px`,
                           transform: `rotate(${angle + 180}deg)`,
                           left: '50%',
                           top: '50%'
                        }}
                    />
                  </motion.div>
                );
             })}

             {/* Background Glows */}
             <div className="absolute inset-0 bg-linear-to-tr from-primary/10 via-purple-500/5 to-transparent blur-3xl -z-10" />
          </div>

        </div>
      </div>
    </section>
  );
}
