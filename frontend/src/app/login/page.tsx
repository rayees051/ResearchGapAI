"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { Brain, Lock, Mail, AlertTriangle, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function Login() {
  const router = useRouter();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isSignUp) {
        // Register new account, then login
        await api.register(email, password);
        await api.login(email, password);
      } else {
        // Login existing account
        await api.login(email, password);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "An authentication error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mesh-grid min-h-screen flex items-center justify-center px-4 relative text-white">
      {/* Decorative Blur Orbs */}
      <div className="absolute top-1/3 left-1/3 w-72 h-72 bg-purple-600/10 rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-1/3 right-1/3 w-72 h-72 bg-indigo-600/10 rounded-full blur-3xl -z-10"></div>

      <div className="w-full max-w-md glass p-8 rounded-2xl shadow-2xl relative border border-white/5">
        
        {/* Branding header */}
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-purple-600/20 border border-purple-500/30 rounded-xl mb-4">
            <Brain className="w-8 h-8 text-purple-400" />
          </div>
          <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-indigo-300 bg-clip-text text-transparent">
            {isSignUp ? "Create Workspace Account" : "Access Research Workspace"}
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            {isSignUp ? "Register email to synthesize publications" : "Sign in to identify scientific knowledge gaps"}
          </p>
        </div>

        {/* Form Error Banner */}
        {error && (
          <div className="flex items-start gap-3 bg-red-950/40 border border-red-500/20 text-red-300 p-4 rounded-xl text-sm mb-6 animate-fadeIn">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                <Mail className="w-4 h-4" />
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@university.edu"
                className="w-full bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl py-3 pl-10 pr-4 text-white text-sm outline-none transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                <Lock className="w-4 h-4" />
              </span>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl py-3 pl-10 pr-4 text-white text-sm outline-none transition-all placeholder:text-slate-600"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold py-3.5 rounded-xl transition-all shadow-lg shadow-purple-500/10 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            {loading ? "Processing..." : isSignUp ? "Create Workspace Account" : "Access Workspace"}
            {!loading && <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />}
          </button>
        </form>

        {/* Tab switcher */}
        <div className="text-center mt-6 pt-6 border-t border-slate-800/40 text-sm">
          <span className="text-slate-400">
            {isSignUp ? "Already registered?" : "New to the framework?"}{" "}
          </span>
          <button
            onClick={() => {
              setIsSignUp(!isSignUp);
              setError(null);
            }}
            className="text-purple-400 hover:text-purple-300 font-semibold cursor-pointer underline underline-offset-4"
          >
            {isSignUp ? "Sign In instead" : "Create an account"}
          </button>
        </div>
      </div>
    </div>
  );
}
