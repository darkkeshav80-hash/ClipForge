/**
 * Time utility functions for formatting and parsing timestamps.
 */

/**
 * Formats a duration in seconds to HH:MM:SS or MM:SS.
 * If forceHours is true or seconds >= 3600, outputs HH:MM:SS.
 */
export function secondsToHms(totalSeconds: number, forceHours: boolean = false): string {
  if (isNaN(totalSeconds) || totalSeconds < 0) totalSeconds = 0;
  const rounded = Math.floor(totalSeconds);
  const h = Math.floor(rounded / 3600);
  const m = Math.floor((rounded % 3600) / 60);
  const s = Math.floor(rounded % 60);

  if (h > 0 || forceHours) {
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

/**
 * Parses a string in HH:MM:SS, MM:SS, or SS format to seconds.
 */
export function hmsToSeconds(hms: string): number {
  if (!hms) return 0;
  const clean = hms.trim();
  const parts = clean.split(':').map((p) => parseFloat(p) || 0);

  if (parts.length === 3) {
    return parts[0] * 3600 + parts[1] * 60 + parts[2];
  } else if (parts.length === 2) {
    return parts[0] * 60 + parts[1];
  } else if (parts.length === 1) {
    return parts[0];
  }
  return 0;
}

/**
 * Clamps a numeric value between min and max bounds.
 */
export function clamp(val: number, min: number, max: number): number {
  if (isNaN(val)) return min;
  return Math.min(Math.max(val, min), max);
}
