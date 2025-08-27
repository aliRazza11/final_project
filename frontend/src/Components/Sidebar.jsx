import { Menu as MenuIcon, LogOut, Settings, Download, Trash2 } from "lucide-react";
import { forceDownload } from "../utils/download"; // 👈 make sure you created this helper
import { useNavigate } from "react-router-dom";

export default function Sidebar({
  collapsed,
  setCollapsed,
  history,
  onDeleteItem,
  onSettings,
  onLogout,
}) {
  const navigate = useNavigate();

  return (
<aside
  className={`fixed inset-y-0 left-0 z-40 flex flex-col
              transition-all duration-300
              ${collapsed ? "w-16" : "w-64"}
              bg-gray-900 text-white border-r border-zinc-200`}
>
      {/* Top bar */}
      <div className="flex items-center justify-between p-4 border-b border-zinc-700/50">
        {!collapsed && <span className="text-lg font-bold">DiffusionApp</span>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 hover:bg-white/10 rounded"
        >
          <MenuIcon size={20} />
        </button>
      </div>

      {/* History list */}
      {!collapsed && (
        <nav className="flex-1 overflow-y-auto p-2 space-y-2">
          {history.map((item) => (
            <div
              key={item.id}
              className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-white/10 group cursor-pointer"
              onClick={() => {
                // 👇 navigate to dashboard with selected image
                navigate("/dashboard", { state: { image: item } });
              }}
            >
              <span className="truncate text-sm text-zinc-200">{item.name}</span>
              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition">
                {/* Download */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    forceDownload(item.downloadHref, item.name);
                  }}
                  className="p-1 hover:bg-white/20 rounded"
                >
                  <Download size={16} />
                </button>

                {/* Delete */}
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
      )}

      {/* Bottom actions */}
      <div className="p-2 border-t border-zinc-700/50 flex flex-col gap-1 mt-auto">
        <button
          onClick={onSettings}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-zinc-200"
        >
          <Settings size={18} />
          {!collapsed && <span>Settings</span>}
        </button>
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/10 text-sm text-zinc-200"
        >
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
