"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, removeAuthToken } from "@/lib/api-client";
import { Brain, Plus, LogOut, Loader2, ArrowRight, FolderClosed, BookOpen, SearchCode, Calendar } from "lucide-react";

interface Project {
  id: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // Create Modal Fields
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
    } catch (err) {
      // API client helper handles 401 redirects
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleLogout = () => {
    removeAuthToken();
    router.push("/login");
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setCreateError(null);

    try {
      const newProj = await api.createProject(title, description);
      setProjects([newProj, ...projects]);
      setShowCreateModal(false);
      setTitle("");
      setDescription("");
      // Route immediately to the new project workspace
      router.push(`/projects/${newProj.id}`);
    } catch (err: any) {
      setCreateError(err.message || "Failed to create project");
    } finally {
      setCreateLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="mesh-grid min-h-screen flex flex-col items-center justify-center text-white">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin mb-4" />
        <p className="text-slate-400 text-sm">Synchronizing workspace metadata...</p>
      </div>
    );
  }

  return (
    <div className="mesh-grid min-h-screen text-white pb-16">
      
      {/* Header navbar */}
      <header className="border-b border-slate-800/40 bg-slate-950/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-purple-600/20 border border-purple-500/30 rounded-xl">
              <Brain className="w-5 h-5 text-purple-400" />
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-purple-400 to-indigo-300 bg-clip-text text-transparent">
              ResearchGap.AI
            </span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-medium px-4 py-2 rounded-xl hover:bg-white/5 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </header>

      {/* Dashboard container */}
      <main className="max-w-7xl mx-auto px-6 mt-10">
        
        {/* Statistics Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="glass p-6 rounded-2xl flex items-center gap-5">
            <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
              <FolderClosed className="w-6 h-6" />
            </div>
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Active Projects</p>
              <h4 className="text-2xl font-bold mt-1">{projects.length}</h4>
            </div>
          </div>
          <div className="glass p-6 rounded-2xl flex items-center gap-5">
            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Publications Ingested</p>
              <h4 className="text-2xl font-bold mt-1">
                {projects.length * 5} <span className="text-xs text-slate-500 font-normal">est.</span>
              </h4>
            </div>
          </div>
          <div className="glass p-6 rounded-2xl flex items-center gap-5">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
              <SearchCode className="w-6 h-6" />
            </div>
            <div>
              <p className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Identified Gaps</p>
              <h4 className="text-2xl font-bold mt-1">
                {projects.filter(p => p.status === "completed").length * 3} <span className="text-xs text-slate-500 font-normal">saved</span>
              </h4>
            </div>
          </div>
        </section>

        {/* Section title & Create project */}
        <section className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Research Spaces</h2>
            <p className="text-slate-400 text-sm mt-1">Select a workspace below or spawn a new discovery graph.</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold px-5 py-2.5 rounded-xl transition-all cursor-pointer shadow-lg shadow-purple-500/15"
          >
            <Plus className="w-4 h-4" />
            New Workspace
          </button>
        </section>

        {/* Projects Cards Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {projects.length === 0 ? (
            <div className="col-span-3 glass p-12 text-center rounded-2xl border-dashed border-slate-800">
              <FolderClosed className="w-12 h-12 text-slate-600 mx-auto mb-4" />
              <h3 className="font-bold text-lg mb-2">No active research workspaces</h3>
              <p className="text-slate-400 text-sm max-w-sm mx-auto mb-6">
                Initialize your first project space to query scholar databases and start analyzing publications.
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="inline-flex items-center gap-2 bg-purple-600/25 border border-purple-500/35 hover:bg-purple-600/35 text-purple-300 font-semibold px-5 py-2.5 rounded-xl transition-all cursor-pointer"
              >
                Create Workspace
              </button>
            </div>
          ) : (
            projects.map((proj) => (
              <div
                key={proj.id}
                onClick={() => router.push(`/projects/${proj.id}`)}
                className="glass p-6 rounded-2xl cursor-pointer glass-hover flex flex-col justify-between h-56 group"
              >
                <div>
                  <div className="flex items-start justify-between">
                    <h3 className="font-bold text-lg group-hover:text-purple-400 transition-colors line-clamp-1">
                      {proj.title}
                    </h3>
                    <span
                      className={`text-xs px-2.5 py-1 rounded-full font-semibold border ${
                        proj.status === "completed"
                          ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400"
                          : proj.status === "running"
                          ? "bg-blue-500/10 border-blue-500/25 text-blue-400 animate-pulse"
                          : proj.status === "failed"
                          ? "bg-red-500/10 border-red-500/25 text-red-400"
                          : "bg-slate-500/10 border-slate-500/25 text-slate-400"
                      }`}
                    >
                      {proj.status}
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm mt-3 line-clamp-3 leading-relaxed">
                    {proj.description || "No description provided. Run the discovery agent using the project title as seed context."}
                  </p>
                </div>
                
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-800/40 text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>{new Date(proj.created_at).toLocaleDateString()}</span>
                  </div>
                  <span className="flex items-center gap-1 font-semibold text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    Open Space
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))
          )}
        </section>
      </main>

      {/* Creation Modal Overlay */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="w-full max-w-lg glass p-8 rounded-2xl border border-white/5 relative">
            <h3 className="text-xl font-bold mb-2">Initialize Research Workspace</h3>
            <p className="text-slate-400 text-sm mb-6">Provide the topic or draft thesis. The system will use this text as search seeds for query retrievals.</p>

            {createError && (
              <div className="bg-red-950/40 border border-red-500/20 text-red-300 p-4 rounded-xl text-sm mb-6">
                {createError}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-5">
              <div>
                <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Project Title / Target Topic
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Cooperative Multi-Agent Benchmarking"
                  className="w-full bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl py-3 px-4 text-white text-sm outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Context / Brief Thesis Statement
                </label>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summarize the core query parameters. This will guide paper critiques and gap analysis constraints..."
                  className="w-full bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl py-3 px-4 text-white text-sm outline-none transition-all resize-none"
                />
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="flex-1 glass hover:bg-white/5 text-slate-300 py-3 rounded-xl transition-all cursor-pointer font-semibold text-center text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold py-3 rounded-xl transition-all cursor-pointer text-center text-sm disabled:opacity-50"
                >
                  {createLoading ? "Spawning Space..." : "Spawn Workspace"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
