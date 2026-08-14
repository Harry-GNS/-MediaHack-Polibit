import { ArrowRight } from "lucide-react";

interface EvidenceCardProps {
  id: string;
  candidateName: string;
  title: string;
  action: string;
  deadline: string;
  budget: string;
  accentColorClass?: string;
  onAuditClick: () => void;
}

export default function EvidenceCard({
  id,
  candidateName,
  title,
  action,
  deadline,
  budget,
  accentColorClass = "bg-accent",
  onAuditClick
}: EvidenceCardProps) {
  return (
    <div className="tech-corners glass p-6 relative group hover:bg-surfaceHover transition-colors text-white text-left">
      <div className="corner-bottom"></div>
      
      {/* Lazo de color */}
      <div className={`absolute top-0 left-0 w-1 h-full opacity-60 ${accentColorClass}`}></div>
      
      <div className="flex justify-between items-start mb-6">
        <span className="font-mono text-[10px] text-gray-500 tracking-widest">[{id}]</span>
        <span className="px-2 py-1 bg-surface text-[10px] font-mono border border-border text-white tracking-wider uppercase">
          {candidateName}
        </span>
      </div>
      
      <h3 className="text-2xl font-light mb-4">{title}</h3>
      
      <div className="space-y-3 font-mono text-sm mb-6">
        <div className="flex justify-between border-b border-border pb-1">
          <span className="text-gray-500">Acción</span>
          <span className="text-white">{action}</span>
        </div>
        <div className="flex justify-between border-b border-border pb-1">
          <span className="text-gray-500">Plazo</span>
          <span className="text-white">{deadline}</span>
        </div>
        <div className="flex justify-between border-b border-border pb-1">
          <span className="text-gray-500">Presupuesto</span>
          <span className={budget === "No especificado" ? "text-yellow-500/80" : "text-white"}>
            {budget}
          </span>
        </div>
      </div>
      
      <button 
        onClick={onAuditClick}
        className="w-full py-2.5 border border-border text-xs font-medium hover:bg-white hover:text-dark transition-all flex justify-center items-center gap-2 group-hover:border-white/30"
      >
        Auditar Histórico
        <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-1" />
      </button>
    </div>
  );
}
