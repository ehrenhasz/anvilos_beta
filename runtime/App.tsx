
import React, { useState, useEffect } from 'react';
import { AgentRole, SystemStatus, LogEntry, RFC, BicameralConfig } from './types';
import { Terminal } from './components/Terminal';
import { CodeAuditor } from './components/CodeAuditor';
import { BlackBoxTest } from './components/BlackBoxTest';
import { SystemConfig } from './components/SystemConfig';
import { DeploymentTerminal } from './components/DeploymentTerminal';
import { Vault } from './components/Vault';

const INITIAL_STATUS: SystemStatus = {
  project: 'BICAMERAL_V102',
  clearance: 'OMEGA',
  mode: 'ACTIVE',
  target: 'LOCAL',
  sshStatus: 'SECURE'
};

const INITIAL_CONFIG: BicameralConfig = {
  model: 'gemini-1.5-pro',
  temperature: 0.7,
  topP: 0.9,
  topK: 40,
  apiTier: 'FREE',
  voiceEnabled: false,
  zoomLevel: 1.0,
  highVisibility: false
};

const App: React.FC = () => {
  const [activeAgent, setActiveAgent] = useState<AgentRole>(AgentRole.COMMANDER);
  const [selectedRFC, setSelectedRFC] = useState<RFC | null>(null);
  const [viewMode, setViewMode] = useState<'terminal' | 'audit' | 'black_ops' | 'config' | 'deploy' | 'vault'>('terminal');
  const [config, setConfig] = useState<BicameralConfig>(INITIAL_CONFIG);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const [sessionClosed, setSessionClosed] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([
    { id: '1', timestamp: '2026-01-11 14:02', message: '☣️ INCIDENT 01: The Guillotine detected.', type: 'incident' },
    { id: '5', timestamp: '2026-01-11 17:15', message: '🕶️ BLACK OPS PROTOCOL ACTIVATED.', type: 'blackops' },
    { id: '6', timestamp: '2026-01-11 18:00', message: '📡 AGENT_DESIGNATION: $AIMEAT online.', type: 'info' },
  ]);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    document.documentElement.style.setProperty('--app-zoom', config.zoomLevel.toString());
  }, [config.zoomLevel]);

  const addLog = (message: string, type: LogEntry['type']) => {
    setLogs(prev => [{ id: Date.now().toString(), timestamp: new Date().toLocaleTimeString(), message, type }, ...prev].slice(0, 10));
  };

  const handleExit = () => {
    addLog("Initiating session teardown...", "warning");
    setTimeout(() => setSessionClosed(true), 1500);
  };

  const borderClass = config.highVisibility ? 'border-4' : 'border';
  const textClass = config.highVisibility ? 'text-lg font-black' : 'text-sm';
  const headerTextClass = config.highVisibility ? 'text-3xl' : 'text-xl';

  if (sessionClosed) {
    return (
      <div className="h-full w-full flex flex-col items-center justify-center bg-black text-green-500 font-mono text-center p-10">
        <h1 className="text-4xl mb-6 flicker">CONNECTION_TERMINATED</h1>
        <p className="text-xl mb-10 opacity-50">All umbilical links severed. Local cache purged.</p>
        <button 
          onClick={() => { setSessionClosed(false); setConfig(INITIAL_CONFIG); }} 
          className="border border-green-500 px-6 py-3 hover:bg-green-500 hover:text-black transition-all"
        >
          RE-ESTABLISH_CONNECTION
        </button>
      </div>
    );
  }

  return (
    <div className={`h-full w-full p-2 flex flex-col bg-black text-green-500 font-mono transition-all duration-300 ${config.highVisibility ? 'p-4' : 'p-2'}`}>
      
      {/* WINDOW TITLE BAR */}
      <div className={`flex-none bg-green-900/20 border-t border-l border-r border-green-500 flex justify-between items-center px-4 py-2 select-none ${borderClass}`}>
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
          <span className="text-xs font-bold tracking-widest opacity-70 uppercase orbitron">$MEAT@BICAMERAL_V102: ~/{viewMode}</span>
        </div>
        <div className="flex items-center gap-6">
           <div className="flex items-center gap-3 bg-black/50 px-3 py-1 border border-green-900">
             <span className="text-[10px] font-black opacity-50">VISIBILITY</span>
             <button 
              onClick={() => setConfig(prev => ({...prev, highVisibility: !prev.highVisibility}))}
              className={`text-[10px] px-2 py-0.5 border ${config.highVisibility ? 'bg-green-500 text-black' : 'border-green-700 opacity-40'}`}
             >
               {config.highVisibility ? 'MAX' : 'STD'}
             </button>
           </div>
           <button onClick={handleExit} className="text-xs hover:text-red-500 font-black transition-colors">[DISCONNECT]</button>
        </div>
      </div>

      <div className={`flex-1 flex flex-col gap-2 border border-green-500 bg-black/90 p-3 overflow-hidden ${borderClass} shadow-[0_40px_100px_rgba(0,0,0,1)]`}>
        
        {/* HEADER */}
        <header className={`flex-none flex justify-between items-center border-b border-green-900 pb-3 mb-2 ${config.highVisibility ? 'mb-6 pb-6' : 'mb-2 pb-3'}`}>
          <div className="flex items-center gap-4">
            <div className={`orbitron font-black text-green-500 tracking-tighter ${headerTextClass}`}>
              ASCII_THE_BLACK_BOX <span className="text-[10px] font-normal opacity-30">V102.0</span>
            </div>
            {config.highVisibility && (
              <div className="bg-red-600 text-black px-4 py-1 font-black animate-pulse">
                HIGH_VIS_ACTIVE
              </div>
            )}
          </div>
          <div className="flex items-center gap-6 text-right">
            <div className="flex flex-col">
              <span className={`font-black tabular-nums tracking-widest ${config.highVisibility ? 'text-3xl' : 'text-xl'}`}>{currentTime}</span>
              <span className="text-[10px] opacity-40 uppercase">Umbilical_link_stable</span>
            </div>
          </div>
        </header>

        {/* NAVIGATION */}
        <nav className="flex-none flex gap-2 mb-2">
          {[
            { id: 'terminal', label: 'COMMS', icon: '📡' },
            { id: 'vault', label: 'VAULT', icon: '📁' },
            { id: 'audit', label: 'ANVIL', icon: '⚒️' },
            { id: 'black_ops', label: 'OPS_TEST', icon: '🕶️' },
            { id: 'deploy', label: 'DEPLOY', icon: '🚀' },
            { id: 'config', label: 'CONFIG', icon: '⚙️' },
          ].map(btn => (
            <button
              key={btn.id}
              onClick={() => setViewMode(btn.id as any)}
              className={`flex-1 py-2 px-1 flex items-center justify-center gap-2 border transition-all ${
                viewMode === btn.id 
                  ? 'bg-green-600 text-black border-green-400' 
                  : 'bg-black border-green-900 text-green-900 hover:border-green-500 hover:text-green-500'
              } ${config.highVisibility ? 'py-4 border-2 text-base' : 'py-2 border text-xs'}`}
            >
              <span>{btn.icon}</span>
              <span className="font-bold orbitron">{btn.label}</span>
            </button>
          ))}
        </nav>

        {/* CONTENT AREA */}
        <div className="flex-1 flex gap-3 min-h-0">
          {/* SIDEBAR */}
          <aside className="w-1/4 flex flex-col gap-3 min-h-0">
            <div className={`bg-black/40 border border-green-900 p-3 flex-none ${borderClass}`}>
              <div className="text-[10px] font-bold mb-3 opacity-30 border-b border-green-900 pb-1 uppercase tracking-widest">Active_Nodes</div>
              <div className="space-y-1.5">
                {Object.entries(AgentRole).map(([key, role]) => (
                  <button
                    key={role}
                    onClick={() => setActiveAgent(role)}
                    className={`w-full text-left p-2 font-bold border transition-all flex justify-between items-center ${
                      activeAgent === role 
                        ? 'bg-green-900/30 border-green-500 text-green-400' 
                        : 'border-green-900/20 text-green-900 hover:border-green-700'
                    } ${textClass}`}
                  >
                    <span>{role === AgentRole.AUDITOR ? '$AIMEAT' : role.toUpperCase()}</span>
                    <span className={`w-2 h-2 rounded-full ${activeAgent === role ? 'bg-green-500 shadow-[0_0_8px_rgba(0,255,65,1)] animate-pulse' : 'bg-green-900/20'}`}></span>
                  </button>
                ))}
              </div>
            </div>

            <div className={`bg-black/40 border border-green-900 p-3 flex-1 flex flex-col min-h-0 overflow-hidden ${borderClass}`}>
              <div className="text-[10px] font-bold mb-3 opacity-30 border-b border-green-900 pb-1 uppercase tracking-widest">RFC_Archive</div>
              <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
                {RFCS.map(rfc => (
                  <div 
                    key={rfc.id}
                    onClick={() => setSelectedRFC(rfc)}
                    className={`p-2 border cursor-pointer transition-all ${selectedRFC?.id === rfc.id ? 'bg-green-900/10 border-green-500' : 'border-green-900/10 text-green-900 hover:border-green-700'} ${textClass}`}
                  >
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-green-500 font-bold">RFC-{rfc.id}</span>
                      <span className="bg-green-900 text-black px-1 text-[8px] font-black">{rfc.status}</span>
                    </div>
                    <div className="truncate opacity-50 text-[10px] italic">{rfc.title}</div>
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* MAIN WORKSPACE */}
          <main className="flex-1 min-h-0 relative">
            <div className={`absolute inset-0 bg-black/60 border border-green-900 p-2 overflow-hidden flex flex-col ${borderClass}`}>
              {viewMode === 'terminal' && <Terminal activeAgent={activeAgent} config={config} />}
              {viewMode === 'audit' && <CodeAuditor config={config} />}
              {viewMode === 'black_ops' && <BlackBoxTest config={config} />}
              {viewMode === 'deploy' && <DeploymentTerminal config={config} onLog={addLog} />}
              {viewMode === 'config' && <SystemConfig config={config} setConfig={setConfig} />}
              {viewMode === 'vault' && <Vault />}
            </div>
          </main>

          {/* RIGHT PANELS (Logs/RFC detail) */}
          <aside className="w-1/4 flex flex-col gap-3 min-h-0">
            <div className={`h-1/2 bg-black/40 border border-green-900 p-3 overflow-hidden flex flex-col ${borderClass}`}>
              {selectedRFC ? (
                <>
                  <div className="flex justify-between border-b border-green-900 pb-1 mb-2">
                    <span className="text-[10px] font-black text-green-500 uppercase">{selectedRFC.title}</span>
                    <button onClick={() => setSelectedRFC(null)} className="text-[10px] hover:text-red-500">X</button>
                  </div>
                  <div className={`flex-1 overflow-y-auto pr-1 custom-scrollbar leading-tight font-bold text-green-700 ${config.highVisibility ? 'text-lg' : 'text-xs'}`}>
                    {selectedRFC.content}
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center text-center opacity-10 grayscale p-10">
                  <span className="text-sm font-black italic tracking-widest uppercase">WAITING_FOR_INDEX...</span>
                </div>
              )}
            </div>

            <div className={`flex-1 bg-black/40 border border-green-900 p-3 overflow-hidden flex flex-col ${borderClass}`}>
              <div className="text-[10px] font-bold mb-3 opacity-30 border-b border-green-900 pb-1 uppercase tracking-widest flex justify-between">
                <span>System_Logs</span>
                <span className="animate-pulse text-green-500">LIVE</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
                {logs.map(log => (
                  <div key={log.id} className={`text-[10px] border-l-2 pl-2 ${
                    log.type === 'incident' ? 'border-red-600 text-red-500' : 
                    log.type === 'deploy' ? 'border-green-400 text-green-400' :
                    'border-green-900 text-green-800'
                  }`}>
                    <div className="flex justify-between font-bold opacity-30 mb-0.5">
                      <span>{log.timestamp}</span>
                      <span>{log.type.toUpperCase()}</span>
                    </div>
                    <div className="font-bold tracking-tight">{log.message}</div>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>

        {/* STATUS FOOTER */}
        <footer className="flex-none flex justify-between items-center bg-green-950/10 border border-green-900 px-4 py-2 mt-2">
           <div className="flex gap-10 items-center">
             <div className="flex items-center gap-2">
               <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
               <span className="text-[10px] font-bold uppercase tracking-widest">System_Sovereign</span>
             </div>
             <span className="text-[10px] opacity-30 font-bold uppercase tracking-widest italic">Umbilical:ratified // PQC_active</span>
           </div>
           <div className="flex gap-4 items-center">
             <div className="flex flex-col items-end mr-4">
                <span className="text-[9px] font-black opacity-30 uppercase">ZOOM</span>
                <input 
                  type="range" min="0.8" max="1.4" step="0.05"
                  value={config.zoomLevel}
                  onChange={(e) => setConfig({ ...config, zoomLevel: parseFloat(e.target.value) })}
                  className="w-24 accent-green-500 h-1 bg-green-950 appearance-none cursor-pointer"
                />
             </div>
             <div className="bg-green-600 text-black px-4 py-1 font-black orbitron text-xs">AUTH: $MEAT</div>
             <button onClick={handleExit} className="bg-red-700 text-white px-4 py-1 font-black orbitron text-xs hover:bg-red-600 transition-all uppercase">EXIT</button>
           </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
