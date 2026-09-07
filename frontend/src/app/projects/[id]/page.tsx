"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import ProjectLogs from "@/components/ProjectLogs";
import CitationNetwork from "@/components/visualization/CitationNetwork";
import GapLandscape from "@/components/visualization/GapLandscape";
import { 
  Brain, ArrowLeft, Loader2, Play, CheckCircle2, AlertOctagon, Trash2, 
  BookOpen, Terminal, Share2, FileText, Upload, Search, HelpCircle, Save 
} from "lucide-react";

export default function ProjectWorkspace() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<any>(null);
  const [papers, setPapers] = useState<any[]>([]);
  const [gaps, setGaps] = useState<any[]>([]);
  const [report, setReport] = useState<string>("");
  
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<"synthesis" | "papers" | "gaps" | "visuals" | "logs">("synthesis");

  // Ingestion fields
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLimit, setSearchLimit] = useState(5);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  // Markdown Edit
  const [editingReport, setEditingReport] = useState(false);
  const [reportContent, setReportContent] = useState("");
  const [savingReport, setSavingReport] = useState(false);

  const fetchWorkspaceData = async () => {
    try {
      const projData = await api.getProject(projectId);
      setProject(projData);
      setReport(projData.synthesis_report || "No report generated yet. Run the pipeline to compile results.");
      setReportContent(projData.synthesis_report || "");
      setRunning(projData.status === "running");

      const papersData = await api.getPapers(projectId);
      setPapers(papersData);

      const gapsData = await api.getGaps(projectId);
      setGaps(gapsData);
    } catch (err) {
      console.error("Error loading workspace data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceData();
  }, [projectId]);

  useEffect(() => {
    let intervalId: any = null;

    if (running || project?.status === "running") {
      intervalId = setInterval(async () => {
        try {
          const projData = await api.getProject(projectId);
          if (projData.status === "completed" || projData.status === "failed") {
            if (intervalId) clearInterval(intervalId);
            setRunning(false);
            setProject(projData);
            setReport(projData.synthesis_report || "No report generated yet. Run the pipeline to compile results.");
            setReportContent(projData.synthesis_report || "");

            const papersData = await api.getPapers(projectId);
            setPapers(papersData);

            const gapsData = await api.getGaps(projectId);
            setGaps(gapsData);

            if (projData.status === "completed") {
              setActiveTab("synthesis");
            }
          } else {
            setProject(projData);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 2000);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [running, project?.status, projectId]);

  const handleDeleteProject = async () => {
    if (confirm("Are you sure you want to delete this workspace and all associated logs and vectors?")) {
      try {
        await api.deleteProject(projectId);
        router.push("/dashboard");
      } catch (err) {
        console.error("Delete failed:", err);
      }
    }
  };

  const handleRunPipeline = async () => {
    try {
      setRunning(true);
      // Trigger execution API
      await api.runProject(projectId);
      // Change tab to logs to monitor step actions
      setActiveTab("logs");
    } catch (err) {
      setRunning(false);
      alert("Failed to initiate graph pipeline.");
    }
  };

  const handlePipelineFinish = async () => {
    // Called when WebSocket stream detects the synthesis_complete log message
    setRunning(false);
    await fetchWorkspaceData();
    setActiveTab("synthesis");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    try {
      const file = e.target.files[0];
      await api.uploadPaper(projectId, file);
      const updatedPapers = await api.getPapers(projectId);
      setPapers(updatedPapers);
    } catch (err) {
      alert("Failed to ingest PDF document.");
    } finally {
      setUploading(false);
    }
  };

  const handleSearchImport = async (e: React.FormEvent) => {
    e.preventDefault();
    setImporting(true);
    setImportError(null);
    try {
      await api.searchAndImportPapers(projectId, searchQuery, searchLimit);
      setSearchQuery("");
      const updatedPapers = await api.getPapers(projectId);
      setPapers(updatedPapers);
    } catch (err: any) {
      setImportError(err.message || "Failed to search and import papers.");
    } finally {
      setImporting(false);
    }
  };

  const handleSaveReport = async () => {
    setSavingReport(true);
    try {
      await api.updateSynthesis(projectId, reportContent);
      setReport(reportContent);
      setEditingReport(false);
    } catch (err) {
      alert("Failed to save synthesis report changes.");
    } finally {
      setSavingReport(false);
    }
  };

  if (loading) {
    return (
      <div className="mesh-grid min-h-screen flex flex-col items-center justify-center text-white">
        <Loader2 className="w-10 h-10 text-purple-500 animate-spin mb-4" />
        <p className="text-slate-400 text-sm">Opening project space...</p>
      </div>
    );
  }

  return (
    <div className="mesh-grid min-h-screen text-white pb-16 flex flex-col">
      
      {/* Header bar */}
      <header className="border-b border-slate-800/40 bg-slate-950/60 backdrop-blur-md sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/dashboard")}
              className="p-2 hover:bg-white/5 rounded-xl text-slate-400 hover:text-white transition-all cursor-pointer"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="font-bold text-lg leading-none">{project?.title}</h1>
                <span
                  className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                    project?.status === "completed"
                      ? "bg-emerald-500/10 border-emerald-500/25 text-emerald-400"
                      : project?.status === "running" || running
                      ? "bg-yellow-500/10 border-yellow-500/25 text-yellow-400 animate-pulse"
                      : project?.status === "failed"
                      ? "bg-red-500/10 border-red-500/25 text-red-400"
                      : "bg-slate-500/10 border-slate-500/25 text-slate-400"
                  }`}
                >
                  {running ? "running" : project?.status}
                </span>
              </div>
              <p className="text-slate-400 text-xs mt-1.5 max-w-xl line-clamp-1">{project?.description}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDeleteProject}
              className="p-2.5 text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 rounded-xl transition-all cursor-pointer"
              title="Delete workspace"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button
              onClick={handleRunPipeline}
              disabled={running || project?.status === "running"}
              className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 disabled:from-slate-800 disabled:to-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-semibold px-5 py-2.5 rounded-xl transition-all shadow-lg shadow-purple-500/15 cursor-pointer"
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Running Pipeline...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Run Discovery
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Failure Banner Notification */}
      {project?.status === "failed" && (
        <div className="max-w-7xl mx-auto px-6 mt-6 w-full animate-fadeIn">
          <div className="flex items-start gap-3 bg-red-950/40 border border-red-500/20 text-red-300 p-4 rounded-xl text-sm">
            <AlertOctagon className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" />
            <div>
              <span className="font-bold block mb-0.5">Discovery Pipeline Failed</span>
              The multi-agent execution pipeline encountered a fatal error while processing this workspace. Please review the **System Trace Logs** tab below for detailed error details.
            </div>
          </div>
        </div>
      )}

      {/* Main Workspace Workspace layout */}
      <main className="max-w-7xl mx-auto px-6 mt-8 flex-grow w-full grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Left column navigation panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="glass p-3.5 rounded-2xl border border-white/5 space-y-1">
            <button
              onClick={() => setActiveTab("synthesis")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "synthesis" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <FileText className="w-4 h-4" />
              Synthesis Draft
            </button>
            <button
              onClick={() => setActiveTab("papers")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "papers" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Ingested Publications
              <span className="ml-auto bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md text-2xs font-bold">
                {papers.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab("gaps")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "gaps" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Brain className="w-4 h-4" />
              Identified Gaps
              <span className="ml-auto bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md text-2xs font-bold">
                {gaps.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab("visuals")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "visuals" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Share2 className="w-4 h-4" />
              Visual Analytics
            </button>
            <button
              onClick={() => setActiveTab("logs")}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "logs" ? "bg-purple-600 text-white" : "text-slate-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Terminal className="w-4 h-4" />
              System Trace Logs
            </button>
          </div>

          {/* Quick Guidance Alert */}
          {papers.length === 0 && (
            <div className="glass p-5 rounded-2xl border-dashed border-purple-500/30 text-xs text-purple-300 leading-relaxed">
              <span className="font-bold text-sm block mb-1">Getting Started</span>
              You can manually upload PDFs or search scholar directories, or click **Run Discovery** directly. If no publications are provided, the agents will automatically fetch relevant papers using external academic directories.
            </div>
          )}
        </div>

        {/* Right column active workspace container */}
        <div className="lg:col-span-3">
          
          {/* Tab 1: Synthesis draft report */}
          {activeTab === "synthesis" && (
            <div className="glass p-8 rounded-2xl border border-white/5 space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800/40 pb-4">
                <div>
                  <h2 className="text-xl font-bold">Synthesized Literature Review</h2>
                  <p className="text-slate-400 text-xs mt-0.5">Edit and finalize the Markdown compilation report generated by agents.</p>
                </div>
                {!editingReport ? (
                  <button
                    onClick={() => {
                      setEditingReport(true);
                      setReportContent(report);
                    }}
                    className="glass px-4 py-2 rounded-xl text-xs font-semibold hover:border-purple-500/50 transition-all cursor-pointer"
                  >
                    Edit Draft
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingReport(false)}
                      className="glass px-4 py-2 rounded-xl text-xs font-semibold hover:bg-white/5 transition-all cursor-pointer text-slate-300"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveReport}
                      disabled={savingReport}
                      className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer"
                    >
                      {savingReport ? <Loader2 className="w-3 animate-spin" /> : <Save className="w-3" />}
                      Save Draft
                    </button>
                  </div>
                )}
              </div>

              {editingReport ? (
                <textarea
                  rows={20}
                  value={reportContent}
                  onChange={(e) => setReportContent(e.target.value)}
                  className="w-full bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl p-5 text-slate-300 text-sm font-mono outline-none transition-all resize-none"
                />
              ) : (
                <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed space-y-4">
                  {report.split("\n").map((line, idx) => {
                    if (line.startsWith("# ")) {
                      return <h1 key={idx} className="text-xl font-bold text-white mt-6 mb-3">{line.replace("# ", "")}</h1>;
                    }
                    if (line.startsWith("## ")) {
                      return <h2 key={idx} className="text-lg font-bold text-white mt-5 mb-2.5">{line.replace("## ", "")}</h2>;
                    }
                    if (line.startsWith("### ")) {
                      return <h3 key={idx} className="text-base font-bold text-slate-200 mt-4 mb-2">{line.replace("### ", "")}</h3>;
                    }
                    if (line.trim() === "") {
                      return <div key={idx} className="h-2" />;
                    }
                    return <p key={idx} className="mb-2.5">{line}</p>;
                  })}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Publications Ingestor */}
          {activeTab === "papers" && (
            <div className="space-y-6">
              
              {/* Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* File Dropzone Upload */}
                <div className="glass p-6 rounded-2xl border border-white/5 flex flex-col justify-between">
                  <div>
                    <h3 className="font-bold text-sm text-slate-300 flex items-center gap-2 mb-2">
                      <Upload className="w-4 h-4 text-purple-400" />
                      Ingest Publication PDFs
                    </h3>
                    <p className="text-slate-400 text-xs leading-relaxed">
                      Upload PDF publications to split paragraphs into sections, run embeddings, and store them locally.
                    </p>
                  </div>
                  
                  <div className="mt-6">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      accept=".pdf"
                      className="hidden"
                    />
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="w-full flex items-center justify-center gap-2 bg-purple-600/10 border border-purple-500/25 hover:bg-purple-600/20 text-purple-300 font-semibold py-3 rounded-xl transition-all cursor-pointer text-sm"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Segmenting PDF...
                        </>
                      ) : (
                        <>
                          <Upload className="w-4 h-4" />
                          Select PDF Document
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* API Search & Import */}
                <div className="glass p-6 rounded-2xl border border-white/5">
                  <h3 className="font-bold text-sm text-slate-300 flex items-center gap-2 mb-2">
                    <Search className="w-4 h-4 text-indigo-400" />
                    Query Academic Directories
                  </h3>
                  <p className="text-slate-400 text-xs leading-relaxed mb-4">
                    Pull metadata, abstract indices, and link structures from arXiv or Semantic Scholar APIs.
                  </p>

                  {importError && (
                    <div className="text-red-300 bg-red-950/20 border border-red-500/15 p-3 rounded-xl text-2xs mb-4">
                      {importError}
                    </div>
                  )}

                  <form onSubmit={handleSearchImport} className="space-y-4">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        required
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search query, e.g. Multi-agent LangGraph"
                        className="flex-grow bg-slate-900/60 border border-slate-800 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 rounded-xl py-2 px-3 text-white text-xs outline-none transition-all"
                      />
                      <button
                        type="submit"
                        disabled={importing}
                        className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-4 rounded-xl text-xs transition-all flex items-center justify-center cursor-pointer"
                      >
                        {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
                      </button>
                    </div>
                  </form>
                </div>
              </div>

              {/* Ingested papers list table */}
              <div className="glass p-6 rounded-2xl border border-white/5">
                <h3 className="font-bold text-base mb-4">Ingested Publications ({papers.length})</h3>
                {papers.length === 0 ? (
                  <div className="py-12 text-center text-slate-500 text-xs">
                    No publications associated with this research space yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-slate-800/60 text-slate-500 uppercase tracking-wider font-semibold">
                          <th className="py-3 pr-4">Title</th>
                          <th className="py-3 px-4">Authors</th>
                          <th className="py-3 px-4">Year</th>
                          <th className="py-3 px-4">Source</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/40 text-slate-300">
                        {papers.map((p) => (
                          <tr key={p.id} className="hover:bg-white/1">
                            <td className="py-3.5 pr-4 font-semibold text-white max-w-xs truncate" title={p.title}>
                              {p.title}
                            </td>
                            <td className="py-3.5 px-4 max-w-[150px] truncate" title={p.authors}>
                              {p.authors || "N/A"}
                            </td>
                            <td className="py-3.5 px-4">{p.year || "N/A"}</td>
                            <td className="py-3.5 px-4 text-purple-400">{p.journal || "Uploaded"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tab 3: Research Gaps list */}
          {activeTab === "gaps" && (
            <div className="glass p-8 rounded-2xl border border-white/5 space-y-6">
              <div>
                <h2 className="text-xl font-bold">Identified Gaps ({gaps.length})</h2>
                <p className="text-slate-400 text-xs mt-0.5">Isolated gaps mapped during cross-critique comparative agent analyses.</p>
              </div>

              {gaps.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-xs">
                  No research gaps identified. Execute the pipeline to locate voids.
                </div>
              ) : (
                <div className="space-y-6">
                  {gaps.map((gap, index) => (
                    <div key={gap.id} className="p-5 bg-slate-950/40 border border-slate-800/60 rounded-xl space-y-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <span className="text-slate-500 font-mono text-2xs mr-2">GAP #{index + 1}</span>
                          <h4 className="font-bold text-white text-base mt-1">{gap.title}</h4>
                        </div>
                        <div className="flex gap-2">
                          <span className="bg-purple-500/20 text-purple-300 border border-purple-500/25 px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider text-[9px]">
                            {gap.category}
                          </span>
                          <span className={`border px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider text-[9px] ${
                            gap.severity === "high" ? "bg-red-500/20 border-red-500/25 text-red-300" : "bg-blue-500/20 border-blue-500/25 text-blue-300"
                          }`}>
                            {gap.severity} Impact
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-400 text-sm leading-relaxed">{gap.description}</p>
                      
                      {/* Suggested research directions */}
                      {gap.suggested_directions && gap.suggested_directions.length > 0 && (
                        <div className="border-t border-slate-900 pt-4 space-y-3">
                          <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Suggested Future Work</p>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {gap.suggested_directions.map((d: any, idx: number) => (
                              <div key={idx} className="bg-slate-900/50 p-3 rounded-lg border border-slate-800/40 text-xs space-y-1">
                                <span className="text-purple-400 font-semibold leading-normal">{d.action}</span>
                                <p className="text-slate-500 leading-normal mt-1">Expected Outcome: {d.outcome}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 4: Visual analytics maps */}
          {activeTab === "visuals" && (
            <div className="space-y-6">
              <CitationNetwork papers={papers} />
              <GapLandscape gaps={gaps} />
            </div>
          )}

          {/* Tab 5: System logs terminal */}
          {activeTab === "logs" && (
            <ProjectLogs 
              projectId={projectId} 
              isActive={running || project?.status === "running"} 
              onPipelineFinish={handlePipelineFinish}
            />
          )}

        </div>

      </main>

    </div>
  );
}
