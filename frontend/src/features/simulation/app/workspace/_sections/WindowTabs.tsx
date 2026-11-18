import EmptyPage from "@/features/simulation/components/EmptyPage";
import { useWindowTabsStore } from "@/features/simulation/store/windowsStore";
import { XMarkIcon } from "@heroicons/react/24/outline";
import React,{ useState } from "react";

export default function WindowTabs() {
  const { tabs, active_tab_id, set_active_tab_id, remove_tab, move_tab } =
    useWindowTabsStore();
  const active_tab = tabs.find((t) => t.id === active_tab_id);
  const [dragged_idx, set_dragged_idx] = useState<number | null>(null);
  const [preview_tabs, set_preview_tabs] = useState<typeof tabs | null>(null);
  const [split_view, set_split_view] = useState<{
    left: (typeof tabs)[0];
    right: (typeof tabs)[0];
    left_active_id?: string;
    right_active_id?: string;
  } | null>(null);

  const get_tabs = () => preview_tabs ?? tabs;

  const handle_close = (e: React.MouseEvent, tab_id: string) => {
    e.stopPropagation();
    remove_tab(tab_id);
  };

  const handle_drag_start = (idx: number) => set_dragged_idx(idx);


  const handle_drag_enter = (over_idx: number) => {
    if (dragged_idx === null || dragged_idx === over_idx) return;
    const new_tabs = [...get_tabs()];
    const [dragged_tab] = new_tabs.splice(dragged_idx, 1);
    new_tabs.splice(over_idx, 0, dragged_tab);
    set_preview_tabs(new_tabs);
    set_dragged_idx(over_idx);
  };

  // 拖拽到主区域时，判断是否需要分屏
  const handle_main_drag_over = (e: React.DragEvent<HTMLDivElement>) => {
    // console.log("draggedIdx", draggedIdx);
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragged_idx === null) return;
    const x = e.clientX;
    const width = window.innerWidth;
    if (x < width / 4) {
      // 鼠标在左侧 1/4 区域
      const left_tab = get_tabs()[dragged_idx];
      const right_tab = active_tab;
      if (left_tab && right_tab) {
        set_split_view({ left: left_tab, right: right_tab });
      }
    } else {
      set_split_view(null);
    }
  };

  // 拖拽释放时，清除分屏状态
  const handle_main_drop = () => {
    if (preview_tabs && dragged_idx !== null) {
      const dragged_tab = preview_tabs[dragged_idx];
      const original_index = tabs.findIndex((tab) => tab.id === dragged_tab.id);
      if (original_index >= 0) move_tab(original_index, dragged_idx);
    }
    set_dragged_idx(null);
    set_preview_tabs(null);
  };

  return (
    <div className="select-none flex flex-col h-full w-full min-h-0">
      {/* Tab导航条 */}
      <div className="absolute w-full left-0 top-0 items-center bg-gray-08 backdrop-blur-xs z-5 flex">
        {get_tabs().map((tab, idx) => (
          <div
            key={tab.id}
            className={`flex items-center justify-center px-5 py-2 cursor-pointer text-sm
              ${
                tab.id === active_tab_id
                  ? "bg-gray-07 text-white"
                  : "bg-gray-08 text-gray-04 hover:!text-white"
              }
            `}
            draggable
            onDragStart={(e) => {
              e.dataTransfer.setData("text/plain", "tab");
              e.dataTransfer.effectAllowed = "move";
              handle_drag_start(idx);
            }}
            onDragEnd={handle_main_drop}
            onDragOver={(e) => e.preventDefault()}
            onDragEnter={() => handle_drag_enter(idx)}
            // onDrop={handleDragEnd}
            onClick={() => set_active_tab_id(tab.id)}
          >
            {tab.title}
            <button
              className="ml-2 text-white hover:text-red-500 hover:cursor-pointer"
              onClick={(e) => handle_close(e, tab.id)}
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        ))}
        {get_tabs().length === 0 && <></>}
      </div>

      {/* 内容区域 */}
      <div
        className="relative z-0 flex h-full w-full flex-1 bg-black"
        onDragOver={handle_main_drag_over}
        onDrop={handle_main_drop}
      >
        {split_view?.left && split_view?.right ? (
          <>
            <div className="flex flex-row w-full h-full">
              <div className="w-1/2 h-full border-r border-white/10 overflow-auto">
                {typeof split_view.left.content === "function"
                  ? split_view.left.content()
                  : split_view.left.content}
              </div>
              <div className="w-1/2 h-full overflow-auto">
                {typeof split_view.right.content === "function"
                  ? split_view.right.content()
                  : split_view.right.content}
              </div>
            </div>
          </>
        ) : active_tab ? (
          <div className="w-full h-full">
            {typeof active_tab.content === "function"
              ? active_tab.content()
              : active_tab.content}
          </div>
        ) : (
          <EmptyPage />
        )}
      </div>
    </div>
  );
}
