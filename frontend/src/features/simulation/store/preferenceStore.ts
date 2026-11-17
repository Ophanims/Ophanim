

import { UserInfo } from "@/features/simulation/types";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PreferenceState {
    // General Preferences
    user_info: UserInfo | null;        // 用户信息对象
    language: string;                 // 语言（如 "en", "zh-CN"）
    dark_mode: boolean;                // 是否开启暗黑模式
    auto_save: boolean;                // 是否自动保存
    auto_save_interval: number;         // 自动保存间隔（秒/分钟）
    timezone: string;                 // 时区设置（如 "Asia/Shanghai"）

    // Accessibility
    high_contrast: boolean;            // 高对比度模式
    reduce_motion: boolean;            // 降低动画

    // Canvas & Workspace
    canvas_background_color: string;   // 画布背景颜色
    constell_color: string;
    orb_color: string;
    isl_color: string;
    gs_color: string;
    sgl_color: string;
    roi_color: string;
    swath_color: string;

    // System/UI layout
    show_tooltips: boolean;            // 是否显示提示气泡

    set_user_info: (user_info: UserInfo | null) => void;
    set_language: (language: string) => void;
    set_dark_mode: (dark: boolean) => void;
    set_auto_save: (auto_save: boolean) => void;
    set_auto_save_interval: (interval: number) => void;
    set_timezone: (tz: string) => void;
    set_high_contrast: (high: boolean) => void;
    set_reduce_motion: (reduce: boolean) => void;
    set_canvas_background_color: (color: string) => void;
    set_constell_color: (color: string) => void;
    set_orb_color: (color: string) => void;
    set_isl_color: (color: string) => void;
    set_gs_color: (color: string) => void;
    set_sgl_color: (color: string) => void;
    set_roi_color: (color: string) => void;
    set_swath_color: (color: string) => void;
    set_show_tooltips: (show: boolean) => void;

    // 可选：重置所有设置
    reset: () => void;
}


export const usePreferenceStore = create<PreferenceState>()(
    persist(
        (set) => ({
            // 默认值
            user_info: null,
            language: "en",
            dark_mode: false,
            auto_save: true,
            auto_save_interval: 5,
            timezone: "UTC",
            high_contrast: false,
            reduce_motion: false,
            canvas_background_color: "#ffffff",
            constell_color: "#2196f3",
            orb_color: "#e91e63",
            isl_color: "#4caf50",
            gs_color: "#ff9800",
            sgl_color: "#9c27b0",
            roi_color: "#607d8b",
            swath_color: "#ffeb3b",
            show_tooltips: true,

            // setter 函数
            set_user_info: (user_info) => set({ user_info }),
            set_language: (language) => set({ language }),
            set_dark_mode: (dark_mode) => set({ dark_mode }),
            set_auto_save: (auto_save) => set({ auto_save }),
            set_auto_save_interval: (auto_save_interval) => set({ auto_save_interval }),
            set_timezone: (timezone) => set({ timezone }),
            set_high_contrast: (high_contrast) => set({ high_contrast }),
            set_reduce_motion: (reduce_motion) => set({ reduce_motion }),
            set_canvas_background_color: (canvas_background_color) => set({ canvas_background_color }),
            set_constell_color: (constell_color) => set({ constell_color }),
            set_orb_color: (orb_color) => set({ orb_color }),
            set_isl_color: (isl_color) => set({ isl_color }),
            set_gs_color: (gs_color) => set({ gs_color }),
            set_sgl_color: (sgl_color) => set({ sgl_color }),
            set_roi_color: (roi_color) => set({ roi_color }),
            set_swath_color: (swath_color) => set({ swath_color }),
            set_show_tooltips: (show_tooltips) => set({ show_tooltips }),

            // 重置
            reset: () =>
                set({
                    user_info: null,
                    language: "en",
                    dark_mode: false,
                    auto_save: true,
                    auto_save_interval: 5,
                    timezone: "UTC",
                    high_contrast: false,
                    reduce_motion: false,
                    canvas_background_color: "#ffffff",
                    constell_color: "#2196f3",
                    orb_color: "#e91e63",
                    isl_color: "#4caf50",
                    gs_color: "#ff9800",
                    sgl_color: "#9c27b0",
                    roi_color: "#607d8b",
                    swath_color: "#ffeb3b",
                    show_tooltips: true,
                }),
        }),
        {
            name: "preference-storage",
        }
    )
);
