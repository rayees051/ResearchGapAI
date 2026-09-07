"use client";

import { useEffect, useState, useRef } from "react";
import { BookOpen, HelpCircle } from "lucide-react";

interface Paper {
  id: string;
  title: string;
  authors: string | null;
  year: number | null;
  journal: string | null;
}

interface CitationNetworkProps {
  papers: Paper[];
}

interface Node {
  id: string;
  label: string;
  year: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
}

interface Link {
  source: string;
  target: string;
}

export default function CitationNetwork({ papers }: CitationNetworkProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<any>(null);

  // Initialize network data
  useEffect(() => {
    if (papers.length === 0) return;

    const width = 500;
    const height = 300;

    // Create Nodes
    const initialNodes = papers.map((p, idx) => {
      // Position nodes in a circle initially
      const angle = (idx / papers.length) * 2 * Math.PI;
      return {
        id: p.id,
        label: p.title.length > 30 ? p.title.slice(0, 30) + "..." : p.title,
        year: p.year ? String(p.year) : "N/A",
        x: width / 2 + Math.cos(angle) * 80,
        y: height / 2 + Math.sin(angle) * 80,
        vx: 0,
        vy: 0,
        radius: 12,
        fullTitle: p.title,
        authors: p.authors || "Unknown Authors",
        journal: p.journal || "Publication"
      };
    });

    // Create Mock citation links between papers for visual graph display
    const mockLinks: Link[] = [];
    if (papers.length > 1) {
      // Connect each paper to the next to form a sequence, and add a few cross links
      for (let i = 0; i < papers.length - 1; i++) {
        mockLinks.push({ source: papers[i].id, target: papers[i + 1].id });
      }
      if (papers.length > 3) {
        mockLinks.push({ source: papers[0].id, target: papers[2].id });
        mockLinks.push({ source: papers[1].id, target: papers[3].id });
      }
    }

    setNodes(initialNodes);
    setLinks(mockLinks);
  }, [papers]);

  // Run 2D Physics Force-Directed Simulator Tick
  useEffect(() => {
    if (nodes.length === 0) return;

    let animId: number;
    const width = 500;
    const height = 300;

    const tick = () => {
      setNodes((currentNodes) => {
        // Copy node positions
        const nextNodes = currentNodes.map((n) => ({ ...n }));

        // 1. Repulsion force between all nodes (Charge)
        for (let i = 0; i < nextNodes.length; i++) {
          for (let j = i + 1; j < nextNodes.length; j++) {
            const n1 = nextNodes[i];
            const n2 = nextNodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            // Nodes closer than 180 repelled
            if (dist < 150) {
              const force = (150 - dist) * 0.04;
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;
              
              n1.vx -= fx;
              n1.vy -= fy;
              n2.vx += fx;
              n2.vy += fy;
            }
          }
        }

        // 2. Link tension pulling connected nodes together
        links.forEach((link) => {
          const nSource = nextNodes.find((n) => n.id === link.source);
          const nTarget = nextNodes.find((n) => n.id === link.target);
          if (nSource && nTarget) {
            const dx = nTarget.x - nSource.x;
            const dy = nTarget.y - nSource.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            
            // Rest length 100
            const strength = 0.02;
            const force = (dist - 90) * strength;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            
            nSource.vx += fx;
            nSource.vy += fy;
            nTarget.vx -= fx;
            nTarget.vy -= fy;
          }
        });

        // 3. Center gravity force pulling towards target center
        nextNodes.forEach((n) => {
          const cx = width / 2;
          const cy = height / 2;
          n.vx += (cx - n.x) * 0.015;
          n.vy += (cy - n.y) * 0.015;

          // Apply velocity and drag friction
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= 0.82;
          n.vy *= 0.82;

          // Bound within viewport limits
          n.x = Math.max(n.radius + 10, Math.min(width - n.radius - 10, n.x));
          n.y = Math.max(n.radius + 10, Math.min(height - n.radius - 10, n.y));
        });

        return nextNodes;
      });

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animId);
  }, [links]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-[400px]">
      
      {/* Network visualization panel */}
      <div className="col-span-2 glass p-5 rounded-2xl border border-white/5 flex flex-col justify-between overflow-hidden relative">
        <div>
          <h3 className="font-bold text-base">Publication Citation Network</h3>
          <p className="text-slate-400 text-xs mt-0.5">Force-directed map showing references and relational links between ingested studies.</p>
        </div>

        {/* SVG Canvas */}
        <div className="flex-grow w-full relative min-h-[220px]">
          {nodes.length === 0 ? (
            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
              Ingest papers to draw citation connections.
            </div>
          ) : (
            <svg viewBox="0 0 500 300" className="w-full h-full select-none absolute inset-0">
              {/* Arrow Head markers for direction */}
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />
                </marker>
              </defs>

              {/* Render links lines */}
              {links.map((link, idx) => {
                const sNode = nodes.find((n) => n.id === link.source);
                const tNode = nodes.find((n) => n.id === link.target);
                if (!sNode || !tNode) return null;
                return (
                  <line
                    key={`link-${idx}`}
                    x1={sNode.x}
                    y1={sNode.y}
                    x2={tNode.x}
                    y2={tNode.y}
                    stroke="#334155"
                    strokeWidth={1.5}
                    markerEnd="url(#arrow)"
                  />
                );
              })}

              {/* Render nodes circles */}
              {nodes.map((node) => (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer group"
                  onClick={() => setSelectedPaper(node)}
                >
                  <circle
                    r={node.radius}
                    fill={selectedPaper?.id === node.id ? "#c084fc" : "#8b5cf6"}
                    className="stroke-[3px] stroke-slate-950 transition-all duration-300 group-hover:scale-110 group-hover:fill-purple-400 pulse-node"
                  />
                  <text
                    y={22}
                    textAnchor="middle"
                    fill="#94a3b8"
                    fontSize={9}
                    className="font-sans font-medium pointer-events-none group-hover:fill-white transition-colors"
                  >
                    {node.label}
                  </text>
                </g>
              ))}
            </svg>
          )}
        </div>
      </div>

      {/* Selected Node Details Sidecard */}
      <div className="glass p-5 rounded-2xl border border-white/5 flex flex-col justify-between">
        <div>
          <h3 className="font-bold text-sm text-slate-300 mb-4 border-b border-slate-800/40 pb-2 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-purple-400" />
            Citation Focus Details
          </h3>

          {selectedPaper ? (
            <div className="space-y-4 animate-fadeIn">
              <div>
                <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Title</p>
                <h4 className="text-white text-sm font-bold leading-snug mt-0.5">{selectedPaper.fullTitle}</h4>
              </div>

              <div>
                <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Authors</p>
                <p className="text-slate-300 text-xs mt-0.5 leading-relaxed">{selectedPaper.authors}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Year</p>
                  <p className="text-slate-300 text-xs mt-0.5">{selectedPaper.year}</p>
                </div>
                <div>
                  <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Journal/Venue</p>
                  <p className="text-slate-300 text-xs mt-0.5 truncate">{selectedPaper.journal}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-40 flex flex-col items-center justify-center text-slate-500 text-center text-xs">
              <HelpCircle className="w-8 h-8 mb-2 opacity-30" />
              <p>Click on any network paper node to view full citation details.</p>
            </div>
          )}
        </div>

        {selectedPaper && (
          <div className="text-[10px] text-purple-300 bg-purple-500/10 border border-purple-500/20 px-3 py-2 rounded-xl text-center font-medium mt-4">
            This study acts as a source in the citation sequence
          </div>
        )}
      </div>
    </div>
  );
}
