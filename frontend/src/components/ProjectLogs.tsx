"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api-client";
import { Terminal, Cpu, Loader2, Sparkles, CheckCircle2, AlertOctagon } from "lucide-react";

interface LogEntry {
  timestamp: string;
  agent_name: string;
  step_name: string;
  log_level: string;
  message: string;
}

interface ProjectLogsProps {
  projectId: string;
  isActive: boolean;
  onPipelineFinish?: () => void;
}

export default function ProjectLogs({ projectId, isActive, onPipelineFinish }: ProjectLogsProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [connected, setConnected] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Connect WebSocket
    const wsUrl = api.getWebSocketLogsUrl(projectId);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log("WebSocket connected to log stream");
    };

    ws.onmessage = (event) => {
      try {
        const data: LogEntry = JSON.parse(event.data);
        setLogs((prev) => {
          // Avoid duplicate entries
          const exists = prev.some(
            (l) => l.timestamp === data.timestamp && l.message === data.message
          );
          if (exists) return prev;
          
          const updated = [...prev, data];
          // Check if completion or failure is flagged in log message
          const isFinishLog = 
            (data.agent_name === "SynthesisWriterAgent" && data.step_name === "synthesis_complete") ||
            (data.agent_name === "Supervisor" && data.step_name === "pipeline_failure");

          if (isFinishLog && onPipelineFinish) {
            onPipelineFinish();
          }
          return updated;
        });
      } catch (err) {
        console.error("Error parsing WS log:", err);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("WebSocket disconnected");
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [projectId, onPipelineFinish]);

  useEffect(() => {
    // Auto scroll to bottom on new logs
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case "RetrievalAgent": return "text-purple-400 bg-purple-500/10 border-purple-500/20";
      case "CritiqueAgent": return "text-indigo-400 bg-indigo-500/10 border-indigo-500/20";
      case "GapAnalyzerAgent": return "text-pink-400 bg-pink-500/10 border-pink-500/20";
      case "SynthesisWriterAgent": return "text-blue-400 bg-blue-500/10 border-blue-500/20";
      case "Supervisor": return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      default: return "text-slate-400 bg-slate-500/10 border-slate-500/20";
    }
  };

  return (
    <div className="glass rounded-2xl flex flex-col h-[500px] border border-white/5 overflow-hidden">
      
      {/* Logger Header */}
      <div className="px-5 py-4 border-b border-slate-800/40 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Terminal className="w-5 h-5 text-purple-400" />
          <span className="font-bold text-sm tracking-wider uppercase">Agent Execution Terminal</span>
        </div>
        <div className="flex items-center gap-2">
          {isActive ? (
            <div className="flex items-center gap-1.5 text-xs text-blue-400 font-semibold bg-blue-500/10 border border-blue-500/25 px-2.5 py-1 rounded-full">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Agent Grid Active
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-semibold bg-slate-500/10 border border-slate-500/25 px-2.5 py-1 rounded-full">
              <Cpu className="w-3.5 h-3.5" />
              Idle
            </div>
          )}
        </div>
      </div>

      {/* Terminal log window */}
      <div className="flex-grow overflow-y-auto p-5 space-y-4 font-mono text-xs bg-black/40">
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500">
            <Terminal className="w-8 h-8 mb-2 opacity-40" />
            <p>Waiting for agent pipeline trigger...</p>
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="flex items-start gap-4 border-l border-slate-800 pl-4 py-0.5 animate-fadeIn">
              
              {/* Agent Badge */}
              <div className={`px-2.5 py-1 rounded-md border text-[10px] font-bold tracking-wider uppercase flex-shrink-0 w-28 text-center truncate ${getAgentColor(log.agent_name)}`}>
                {log.agent_name.replace("Agent", "")}
              </div>
              
              {/* Message text */}
              <div className="flex-grow leading-relaxed">
                <span className="text-slate-500 mr-2">[{log.step_name}]</span>
                <span className={log.log_level === "ERROR" ? "text-red-400 font-semibold" : "text-slate-300"}>
                  {log.message}
                </span>
              </div>

              {/* Timestamp */}
              <div className="text-[10px] text-slate-600 flex-shrink-0">
                {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </div>
            </div>
          ))
        )}
        <div ref={logEndRef} />
      </div>
    </div>
  );
}
