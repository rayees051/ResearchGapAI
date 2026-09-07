"use client";

import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface ResearchGap {
  id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
}

interface GapLandscapeProps {
  gaps: ResearchGap[];
}

export default function GapLandscape({ gaps }: GapLandscapeProps) {
  const getSeverityValue = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high": return 3;
      case "medium": return 2;
      case "low": return 1;
      default: return 1;
    }
  };

  const getCategoryIndex = (category: string) => {
    switch (category.toLowerCase()) {
      case "methodological": return 1;
      case "empirical": return 2;
      case "population": return 3;
      case "theoretical": return 4;
      default: return 1;
    }
  };

  const categories = ["", "Methodological", "Empirical", "Population", "Theoretical"];
  const severities = ["", "Low Severity", "Medium Severity", "High Severity"];

  const data = gaps.map((gap) => ({
    x: getCategoryIndex(gap.category),
    y: getSeverityValue(gap.severity),
    z: getSeverityValue(gap.severity) * 10, // sizing bubble
    title: gap.title,
    description: gap.description,
    category: gap.category,
    severity: gap.severity,
  }));

  const getBubbleColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high": return "#ec4899"; // pink
      case "medium": return "#8b5cf6"; // purple/violet
      case "low": return "#3b82f6"; // blue
      default: return "#8b5cf6";
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="glass p-4 rounded-xl max-w-xs border border-white/10 text-xs shadow-xl">
          <p className="font-bold text-white text-sm mb-1">{data.title}</p>
          <div className="flex gap-2 mb-2 mt-1.5">
            <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/20 uppercase tracking-wider font-bold text-[9px]">
              {data.category}
            </span>
            <span className={`px-2 py-0.5 rounded-full border uppercase tracking-wider font-bold text-[9px] ${
              data.severity === "high" ? "bg-red-500/20 border-red-500/20 text-red-300" : "bg-blue-500/20 border-blue-500/20 text-blue-300"
            }`}>
              {data.severity} Impact
            </span>
          </div>
          <p className="text-slate-400 leading-relaxed">{data.description}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="glass p-6 rounded-2xl border border-white/5 flex flex-col h-[400px]">
      
      {/* Title */}
      <div className="mb-4">
        <h3 className="font-bold text-base">Scientific Gap Landscape</h3>
        <p className="text-slate-400 text-xs mt-0.5">Distribution of identified gaps mapped by research dimension and severity.</p>
      </div>

      {/* Chart */}
      <div className="flex-grow w-full h-[280px]">
        {data.length === 0 ? (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm">
            No landscape nodes. Run the agent pipeline first.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
              <XAxis 
                type="number" 
                dataKey="x" 
                name="Category" 
                domain={[0.5, 4.5]}
                tickFormatter={(val) => categories[val] || ""}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
              />
              <YAxis 
                type="number" 
                dataKey="y" 
                name="Severity" 
                domain={[0.5, 3.5]}
                tickFormatter={(val) => severities[val] || ""}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
              />
              <ZAxis type="number" dataKey="z" range={[150, 400]} />
              <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
              <Scatter data={data} fill="#8b5cf6">
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBubbleColor(entry.severity)} className="cursor-pointer hover:opacity-85 transition-opacity" />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legends */}
      <div className="flex gap-4 items-center justify-center text-[10px] text-slate-400 border-t border-slate-800/40 pt-4 mt-2">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-pink-500"></span>
          <span>High Severity Gap</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
          <span>Medium Severity Gap</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
          <span>Low Severity Gap</span>
        </div>
      </div>
    </div>
  );
}
