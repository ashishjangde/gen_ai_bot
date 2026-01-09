import React from 'react'
import { HeroSection } from "./_components/home/hero-section";
import { BentoGridSection } from "./_components/home/bento-grid";
import { FeatureHighlight } from "./_components/home/feature-highlight";

export default function page() {
  return (
    <div className="flex min-h-screen flex-col bg-gray-950">
      <HeroSection />
      <BentoGridSection />
      <FeatureHighlight />
    </div>
  )
}
