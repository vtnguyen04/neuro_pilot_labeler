import { Folder, Plus, Search, Trash2 } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API } from '../api';
import { MainLayout } from '../components/layout/MainLayout';
import { Project } from '../types';

function cn(...classes: (string | boolean | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
  const [selectedProjectIds, setSelectedProjectIds] = useState<Set<number>>(new Set());
  const [mergeName, setMergeName] = useState('');
  const [mergeLoading, setMergeLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    API.labels.getProjects().then(setProjects);
  }, []);

  const handleCreateProject = async () => {
    const name = prompt("Enter project name:");
    if (!name) return;
    try {
        await API.labels.createProject(name);
        const projs = await API.labels.getProjects();
        setProjects(projs);
    } catch (error) {
        console.error("Creation failed:", error);
        alert("Creation failed.");
    }
  };

  const handleMerge = async () => {
    if (selectedProjectIds.size < 2) {
        alert("Please select at least 2 projects to merge.");
        return;
    }
    if (!mergeName) {
        alert("Please enter a name for the new project.");
        return;
    }

    setMergeLoading(true);
    try {
        const result = await API.labels.mergeProjects(Array.from(selectedProjectIds), mergeName);
        if (result.status === 'success') {
            alert("Projects merged successfully!");
            setIsMergeModalOpen(false);
            setSelectedProjectIds(new Set());
            setMergeName('');
            const projs = await API.labels.getProjects();
            setProjects(projs);
        }
    } catch (error) {
        console.error("Merge failed:", error);
        alert("Merge failed.");
    } finally {
        setMergeLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="p-10 max-w-6xl mx-auto space-y-10">
        <header className="flex justify-between items-center">
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2 font-cyber tracking-tight">MY_PROJECTS</h1>
                <p className="text-white/40 uppercase text-[10px] tracking-[0.2em] font-black">Central Intelligence & Dataset Hub</p>
            </div>
            <div className="flex gap-4">
                <button
                    onClick={() => setIsMergeModalOpen(true)}
                    className="bg-white/5 border border-white/20 text-white px-6 py-2.5 rounded-2xl font-bold flex items-center gap-2 hover:bg-white/10 transition-all uppercase text-xs"
                >
                    Merge Projects
                </button>
                <button
                    onClick={handleCreateProject}
                    className="bg-accent text-black px-6 py-2.5 rounded-2xl font-bold flex items-center gap-2 hover:bg-white transition-all shadow-[0_0_30px_rgba(0,255,65,0.3)] uppercase text-xs"
                >
                    <Plus className="w-5 h-5" /> New Project
                </button>
            </div>
        </header>

        <div className="flex gap-4 items-center bg-white/5 p-3 rounded-2xl border border-white/10">
            <div className="flex-1 flex items-center gap-3 px-3">
                <Search className="w-5 h-5 text-white/20" />
                <input placeholder="SEARCH_VECTORS..." className="bg-transparent border-none focus:ring-0 text-sm w-full outline-none font-black tracking-widest text-white/60" />
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {projects.map((proj) => (
                <ProjectCard
                    key={proj.id}
                    title={proj.name}
                    type="Neural Dataset"
                    images={0}
                    models={0}
                    updated="Just now"
                    onClick={() => navigate(`/dataset/${proj.id}`)}
                    onDelete={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        if (confirm(`Delete project "${proj.name}"? This will remove all associated labels.`)) {
                            API.labels.deleteProject(proj.id).then(() => {
                                API.labels.getProjects().then(setProjects);
                            });
                        }
                    }}
                />
            ))}
             <div onClick={handleCreateProject} className="border-4 border-dashed border-white/5 rounded-[2.5rem] flex flex-col items-center justify-center p-12 text-white/10 hover:text-accent/40 hover:border-accent/20 transition-all cursor-pointer group">
                <Plus className="w-16 h-16 mb-4 group-hover:scale-110 transition-transform" />
                <span className="font-black tracking-[0.3em] text-[10px]">CREATE_NEW</span>
             </div>
        </div>
      </div>

      {/* Merge Modal */}
      {isMergeModalOpen && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-xl z-[100] flex items-center justify-center p-6">
            <div className="w-full max-w-2xl bg-[#0a0a0c] border-2 border-white/20 rounded-[3rem] overflow-hidden shadow-[0_0_100px_rgba(0,255,65,0.1)]">
                <div className="p-10 border-b border-white/10 bg-white/5">
                    <h2 className="text-2xl font-black text-white font-cyber tracking-tighter uppercase">Merge_Datasets</h2>
                </div>
                <div className="p-10 space-y-8">
                    <div className="space-y-4">
                        <label className="text-xs font-black text-white/40 uppercase tracking-widest">Target Project Name</label>
                        <input
                            type="text"
                            value={mergeName}
                            onChange={e => setMergeName(e.target.value)}
                            placeholder="Unified_Dataset_v1"
                            className="w-full bg-white/5 border-2 border-white/10 rounded-2xl p-4 text-white font-black outline-none focus:border-accent transition-all"
                        />
                    </div>
                    <div className="space-y-4">
                        <label className="text-xs font-black text-white/40 uppercase tracking-widest">Select Projects to Union ({selectedProjectIds.size})</label>
                        <div className="grid grid-cols-1 gap-2 max-h-64 overflow-y-auto cyber-scrollbar pr-2">
                            {projects.map(p => (
                                <button
                                    key={p.id}
                                    onClick={() => {
                                        const next = new Set(selectedProjectIds);
                                        if (next.has(p.id)) next.delete(p.id);
                                        else next.add(p.id);
                                        setSelectedProjectIds(next);
                                    }}
                                    className={`w-full flex items-center justify-between p-4 rounded-xl border-2 transition-all ${
                                        selectedProjectIds.has(p.id) ? 'bg-accent/20 border-accent text-white' : 'bg-white/5 border-white/5 text-white/40 hover:bg-white/10'
                                    }`}
                                >
                                    <span className="font-bold">{p.name}</span>
                                    <span className="text-[10px] font-mono opacity-40">{p.classes.length} classes</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
                <div className="p-10 bg-white/5 border-t border-white/10 flex gap-4">
                    <button
                        onClick={() => setIsMergeModalOpen(false)}
                        className="flex-1 py-4 rounded-2xl border-2 border-white/10 text-white font-black uppercase tracking-widest hover:bg-white/5 transition-all"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleMerge}
                        disabled={mergeLoading || selectedProjectIds.size < 2 || !mergeName}
                        className="flex-1 py-4 rounded-2xl bg-accent text-black font-black uppercase tracking-widest shadow-[0_0_30px_rgba(0,255,65,0.3)] hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                        {mergeLoading ? 'Processing...' : 'Execute Merge'}
                    </button>
                </div>
            </div>
        </div>
      )}
    </MainLayout>
  );
};

interface ProjectCardProps {
    title: string;
    type: string;
    images: number;
    models: number;
    updated: string;
    active?: boolean;
    onClick: () => void;
    onDelete: (e: React.MouseEvent) => void;
}

const ProjectCard = ({ title, type, images, models, updated, active, onClick, onDelete }: ProjectCardProps) => (
    <div
        onClick={onClick}
        className={cn(
            "bg-white/5 border border-white/10 rounded-2xl p-6 transition-all cursor-pointer group hover:bg-white/[0.08] hover:border-white/20 hover:translate-y-[-4px] relative",
            active && "border-accent/40 bg-accent/[0.02]"
        )}
    >
        <button
            onClick={(e) => { e.stopPropagation(); onDelete(e); }}
            className="absolute top-4 right-4 p-2 text-red-400/60 hover:text-red-500 hover:bg-red-500/20 rounded-lg transition-all z-20 border border-red-500/20 hover:border-red-500/40"
        >
            <Trash2 className="w-4 h-4" />
        </button>
        <div className="flex justify-between items-start mb-6">
            <div className="w-12 h-12 bg-accent/20 rounded-xl flex items-center justify-center">
                <Folder className="w-6 h-6 text-accent" />
            </div>
            <span className="text-[10px] font-cyber text-accent/60 px-2 py-0.5 rounded border border-accent/20 uppercase tracking-tighter">
                {type}
            </span>
        </div>
        <h3 className="text-lg font-bold text-white mb-4 transition-colors group-hover:text-accent">{title}</h3>
        <div className="flex items-center gap-4 text-xs text-white/40 mb-6">
            <span>{images.toLocaleString()} Images</span>
            <div className="w-1 h-1 rounded-full bg-white/10" />
            <span>{models} Models</span>
        </div>
        <div className="pt-4 border-t border-white/5 flex justify-between items-center">
            <span className="text-[10px] text-white/20 uppercase tracking-widest">Edited {updated}</span>
            <div className="flex -space-x-2">
                {[1,2,3].map(i => (
                    <div key={i} className="w-6 h-6 rounded-full border-2 border-[#0a0a0c] bg-white/10 flex items-center justify-center text-[8px] text-white/40">U{i}</div>
                ))}
            </div>
        </div>
    </div>
)
