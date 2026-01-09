"use client";

import { Canvas } from "@react-three/fiber";
import { Stars } from "@react-three/drei";
import {
  motion,
  useMotionTemplate,
  useMotionValue,
  animate,
  AnimatePresence,
} from "motion/react";
import { Search, Mic, ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";

const COLORS_TOP = ["#13FFAA", "#1E67C6", "#CE84CF", "#DD335C"];

const FlipWords = ({ words }: { words: string[] }) => {
  const [currentWord, setCurrentWord] = useState(words[0]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      const nextIndex = (currentIndex + 1) % words.length;
      setCurrentIndex(nextIndex);
      setCurrentWord(words[nextIndex]);
    }, 3000);
    return () => clearInterval(interval);
  }, [currentIndex, words]);

  return (
    <span className="inline-block min-w-[120px] text-left text-primary">
      <AnimatePresence mode="wait">
        <motion.span
          key={currentWord}
          initial={{ opacity: 0, y: 10, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: -10, filter: "blur(8px)" }}
          transition={{ duration: 0.4, ease: "easeInOut" }}
          className="block"
        >
          {currentWord}
        </motion.span>
      </AnimatePresence>
    </span>
  );
};

export function HeroSection() {
  const color = useMotionValue(COLORS_TOP[0]);

  useEffect(() => {
    animate(color, COLORS_TOP, {
      ease: "easeInOut",
      duration: 10,
      repeat: Infinity,
      repeatType: "mirror",
    });
  }, [color]);

  const backgroundImage = useMotionTemplate`radial-gradient(125% 125% at 50% 0%, #020617 50%, ${color})`;

  return (
    <motion.section
      style={{
        backgroundImage,
      }}
      className="relative grid min-h-screen place-content-center overflow-hidden bg-gray-950 px-4 py-24 text-gray-200"
    >
      <div className="relative z-10 flex w-full max-w-4xl flex-col items-center gap-10 text-center">
        {/* Main Headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex flex-col items-center gap-4"
        >
          <h1 className="text-6xl font-bold tracking-tighter text-white sm:text-7xl md:text-8xl lg:text-9xl">
            Ask{" "}
            <FlipWords
              words={["Everything.", "Stocks.", "Code.", "News.", "Reasoning."]}
            />
          </h1>
          <p className="max-w-xl text-lg text-gray-400 sm:text-xl">
            The universal interface for your digital life. Connect files, code,
            and the web in one intelligent conversation.
          </p>
        </motion.div>

        {/* The Omni-Input (Adapted for Dark Aurora Theme) */}
        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ delay: 0.2, duration: 0.5 }}
           className="w-full max-w-2xl px-2"
        >
          <div className="group relative flex items-center gap-3 rounded-2xl border border-white/10 bg-white/5 p-2 pl-5 shadow-2xl backdrop-blur-xl transition-all hover:border-white/20 hover:shadow-primary/10 hover:bg-white/10 focus-within:border-primary/50 focus-within:ring-1 focus-within:ring-primary/20">
             <Search className="h-5 w-5 text-gray-400" />
             <input 
               type="text" 
               placeholder="What can I help you create today?"
               className="flex-1 bg-transparent text-lg text-white placeholder:text-gray-500 focus:outline-none"
             />
             <div className="flex gap-2">
                <button className="hidden rounded-lg p-2 text-gray-400 transition-colors hover:bg-white/10 hover:text-white sm:block">
                  <Mic className="h-5 w-5" />
                </button>
                <div className="h-8 w-[1px] bg-white/10" />
                <button className="flex h-10 items-center gap-2 rounded-xl bg-primary px-5 font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary/90 active:scale-95">
                  Generate
                  <ArrowRight className="h-4 w-4 opacity-50" />
                </button>
             </div>
          </div>
          
          {/* Footer Links */}
          <div className="mt-8 flex justify-center gap-6 text-sm font-medium text-gray-500">
             <span className="cursor-pointer transition-colors hover:text-white">Analyze Data</span>
             <span className="cursor-pointer transition-colors hover:text-white">Write Code</span>
             <span className="cursor-pointer transition-colors hover:text-white">Search Web</span>
          </div>
        </motion.div>
      </div>

      <div className="absolute inset-0 z-0">
        <Canvas>
          <Stars radius={50} count={2500} factor={4} fade speed={2} />
        </Canvas>
      </div>
    </motion.section>
  );
}
