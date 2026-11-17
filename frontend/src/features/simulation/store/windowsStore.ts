import { ReactNode } from "react";
import { create } from "zustand";

export interface WindowTab {
  id: string;
  title: string;
  content: ReactNode | (() => ReactNode);
}

export interface WindowGroup {
  id: number;
  tabs: WindowTab[];
}

interface WindowTabsState {
  tabs: WindowTab[]; // will be removed in the future, use groups instead
  groups: WindowGroup[];
  active_group_id: number;
  active_tab_id: string;
  set_active_tab_id: (id: string) => void;
  add_tab: (tab: WindowTab) => void;
  remove_tab: (tab_id: string) => void;
  initialize: (initial_tabs: WindowTab[]) => void;
  move_tab: (from_idx: number, to_idx: number) => void;
}

export const useWindowTabsStore = create<WindowTabsState>((set, get) => ({
  groups: [],
  tabs: [],
  active_tab_id: "",
  active_group_id: 0,

  set_active_tab_id: (id: string) => set({ active_tab_id: id }),

  addGroup: () => {
    const { groups } = get();
    const group: WindowGroup = {
      id: groups.length + 1, // Unique ID based on array length
      tabs: [],
    };
    set({
      groups: [...groups, group],
      active_group_id: group.id,
      active_tab_id: group.tabs[0]?.id ?? "",
    });
  },

  removeGroup: (group_id: number) => {
    const { groups, active_group_id } = get();
    const new_groups = groups.filter((g) => g.id !== group_id);
    const is_active_removed = active_group_id === group_id;

    set({
      groups: new_groups,
      active_group_id: is_active_removed ? new_groups[0]?.id ?? "" : active_group_id,
      active_tab_id: "",
    });
  },

  add_tab: (tab: WindowTab) => {
    const { tabs } = get();
    const exists = tabs.some((t) => t.id === tab.id);
    if (!exists) {
      set({
        tabs: [...tabs, tab],
        active_tab_id: tab.id,
      });
    } else {
      set({ active_tab_id: tab.id });
    }
  },

  remove_tab: (tab_id: string) => {
    const { tabs, active_tab_id } = get();
    const new_tabs = tabs.filter((t) => t.id !== tab_id);
    const is_active_removed = active_tab_id === tab_id;

    set({
      tabs: new_tabs,
      active_tab_id: is_active_removed ? new_tabs[0]?.id ?? "" : active_tab_id,
    });
  },

  move_tab: (from_idx: number, to_idx: number) => {
    const { tabs } = get();
    if (from_idx < 0 || from_idx >= tabs.length || to_idx < 0 || to_idx >= tabs.length) return;

    const new_tabs = [...tabs];
    const [moved_tab] = new_tabs.splice(from_idx, 1);
    new_tabs.splice(to_idx, 0, moved_tab);

    set({ tabs: new_tabs });
  },

  initialize: (initial_tabs: WindowTab[]) => {
    set({
      tabs: initial_tabs,
      active_tab_id: initial_tabs[0]?.id ?? "",
    });
  },
}));
