/**
 * 将 ISO 字符串（UTC或带时区）转为本地时间字符串，适合 input[type="datetime-local"] 的 value
 * @param isoString 例如 '2025-06-25T01:04:00Z'
 * @returns '2025-06-25T09:04'（本地时间，适合 input）
 */
export function to_input_local(iso_string: string | Date): string {
    if (!iso_string) return "";
    const date = typeof iso_string === "string" ? new Date(iso_string) : iso_string;
    // 本地时间部分
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hour = String(date.getHours()).padStart(2, "0");
    const minute = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hour}:${minute}`;
}

/**
 * 将 input[type="datetime-local"] 的本地时间字符串转为 UTC ISO 字符串，适合后端和 Skyfield
 * @param localStr 例如 '2025-06-25T09:04'
 * @returns '2025-06-25T01:04:00.000Z'（UTC ISO字符串）
 */
export function local_to_utciso_string(local_str: string): string {
    if (!local_str) return "";
    // localStr 没有时区，直接 new Date 会被当成本地时间
    const date = new Date(local_str);
    return date.toISOString();
}