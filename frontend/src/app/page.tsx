"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getAuthToken } from "@/lib/api-client";
import { Search, Brain, Share2, Layers, ArrowRight } from "lucide-react";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(!!getAuthToken());
  }, []);

  return (
    <div className="mesh-grid min-h-screen flex flex-col justify-between text-white relative">
      {/* Background shapes */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -z-10 animate-pulse"></div>

      {/* Header */}
      <header className="w-full max-w-7xl mx-auto px-6 py-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-purple-600/20 border border-purple-500/30 rounded-xl">
            <Brain className="w-6 h-6 text-purple-400" />
          </div>
          <span className="font-bold text-xl tracking-tight bg-gradient-to-r from-purple-400 to-indigo-300 bg-clip-text text-transparent">
            ResearchGap.AI
          </span>
        </div>
        <Link
          href={isAuthenticated ? "/dashboard" : "/login"}
          className="glass px-5 py-2 rounded-xl text-sm font-semibold hover:border-purple-500/50 transition-all"
        >
          {isAuthenticated ? "Go to Dashboard" : "Sign In"}
        </Link>
      </header>

      {/* Hero Body */}
      <main className="max-w-4xl mx-auto px-6 py-16 text-center z-10 flex flex-col items-center justify-center flex-grow">
        {/* Project Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-xs font-semibold tracking-wide uppercase mb-8">
          <span className="w-2 h-2 rounded-full bg-purple-400 animate-ping"></span>
          Major Project Blueprint
        </div>

        {/* Headline */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight mb-8">
          Adaptive Multi-Agent Framework for{" "}
          <span className="block bg-gradient-to-r from-purple-400 via-indigo-300 to-blue-400 bg-clip-text text-transparent mt-1">
            Automated Research Gap Identification
          </span>
        </h1>

        {/* Description */}
        <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed mb-12">
          Empower your scientific review workflows. Ingest databases, parse PDFs, and let cooperative, stateful LangGraph agents contrast methodology limits to isolate knowledge voids.
        </p>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16 justify-center">
          <Link
            href={isAuthenticated ? "/dashboard" : "/login"}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold px-8 py-4 rounded-xl shadow-lg shadow-purple-500/20 transition-all group"
          >
            Launch Workspace 
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <a
            href="#features"
            className="glass hover:bg-white/5 text-slate-300 font-semibold px-8 py-4 rounded-xl transition-all"
          >
            Explore Agent Loop
          </a>
        </div>

        {/* Features grid */}
        <div id="features" className="grid grid-cols-1 md:grid-cols-4 gap-6 w-full max-w-5xl mt-8">
          <div className="glass p-6 rounded-2xl text-left glass-hover">
            <Search className="w-6 h-6 text-purple-400 mb-4" />
            <h3 className="font-semibold text-lg mb-2">Ingestion Agent</h3>
            <p className="text-sm text-slate-400">Queries arXiv/Semantic Scholar API and indexes parsed paper layouts.</p>
          </div>
          <div className="glass p-6 rounded-2xl text-left glass-hover">
            <Layers className="w-6 h-6 text-indigo-400 mb-4" />
            <h3 className="font-semibold text-lg mb-2">Critique Agent</h3>
            <p className="text-sm text-slate-400">Extracts study limits, dataset bounds, and parameter constraints.</p>
          </div>
          <div className="glass p-6 rounded-2xl text-left glass-hover">
            <Brain className="w-6 h-6 text-pink-400 mb-4" />
            <h3 className="font-semibold text-lg mb-2">Analyzer Agent</h3>
            <p className="text-sm text-slate-400">Maps methodology contradictions and identifies scientific gaps.</p>
          </div>
          <div className="glass p-6 rounded-2xl text-left glass-hover">
            <Share2 className="w-6 h-6 text-blue-400 mb-4" />
            <h3 className="font-semibold text-lg mb-2">Synthesis Writer</h3>
            <p className="text-sm text-slate-400">Compiles findings into formatted Markdown synthesis reports.</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full border-t border-slate-800/40 py-6 text-center text-sm text-slate-500 z-10">
        © 2026 Adaptive Multi-Agent Framework. Designed for Major Project Evaluation.
      </footer>
    </div>
  );
}
