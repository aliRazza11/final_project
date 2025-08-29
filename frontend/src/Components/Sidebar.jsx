import {
  Menu as MenuIcon,
  LogOut,
  Settings,
  Download,
  Trash2,
  X,
} from "lucide-react";
import { forceDownload } from "../utils/download";
import { useNavigate } from "react-router-dom";

export default function Sidebar({
  collapsed,
  setCollapsed,
  history,
  onDeleteItem,
  onSettings,
  onLogout,
  sidebarOpen,     
  setSidebarOpen,  
}) {
  const navigate = useNavigate();

  return (
    <aside
      className={`
        fixed inset-y-0 left-0 z-50 flex flex-col
        bg-gray-900 text-white border-r border-zinc-200
        transition-transform duration-300
        ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0
        ${collapsed ? "md:w-16" : "md:w-64"} w-64
        overflow-x-hidden   
      `}
    >
   
      <div className="flex items-center justify-between p-4 border-b border-zinc-700/50">
        {!collapsed && (
          <span className="text-lg font-bold hidden md:inline">
            DiffusionApp
          </span>
        )}
        <div className="flex gap-2">
     
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden md:block p-1 hover:bg-white/10 rounded"
          >
            <MenuIcon size={20} />
          </button>

          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden p-1 hover:bg-white/10 rounded"
          >
            <X size={20} />
          </button>
        </div>
      </div>


      <nav className="flex-1 p-2 space-y-2 md:overflow-y-auto">
        {history.map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/10 group cursor-pointer overflow-hidden"
            onClick={() => {
              navigate("/dashboard", { state: { image: item } });
              setSidebarOpen(false); // close sidebar on mobile after click
            }}
          >
            <span className="truncate text-sm text-zinc-200">
              {item.name}
            </span>
            <div className="flex gap-2 flex-shrink-0 opacity-0 group-hover:opacity-100 transition">
    
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  forceDownload(item.downloadHref, item.name);
                }}
                className="p-1 hover:bg-white/20 rounded"
              >
                <Download size={16} />
              </button>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteItem(item);
                }}
                className="p-1 hover:bg-red-500/80 rounded"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </nav>

  
      <div className="p-2 border-t border-zinc-700/50 flex flex-col gap-1 mt-auto">
        <button
          onClick={() => {
            onSettings();
            setSidebarOpen(false);
          }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-zinc-200"
        >
          <Settings size={18} />
          {!collapsed && <span className="hidden md:inline">Settings</span>}
        </button>
        <button
          onClick={() => {
            onLogout();
            setSidebarOpen(false);
          }}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-zinc-200"
        >
          <LogOut size={18} />
          {!collapsed && <span className="hidden md:inline">Logout</span>}
        </button>
      </div>
    </aside>
  );
}
