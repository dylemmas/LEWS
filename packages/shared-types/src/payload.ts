// 19-byte binary payload layout — shared with backend services and simulator.
// Spec: severity(1) | sensor_mask(1) | rain_tips(2) | accel_rms(2) | tilt(2) |
//       crack(2) | lat(4) | lon(4) | battery(2) = 20 bytes ... actually 20.
// (Spec is 19 in the PPT; we implement 20 for an even payload — see backend notes.)

import { Severity } from './enums';

export const SENSOR_MASK = {
  RAIN: 1 << 0,
  ACCEL: 1 << 1,
  TILT: 1 << 2,
  CRACK: 1 << 3,
  GPS: 1 << 4,
  BATTERY: 1 << 5,
} as const;

export interface DecodedReading {
  severity: Severity;
  sensor_mask: number;
  rain_tips_15m: number;
  accel_rms_mg: number;
  tilt_delta_ddeg: number;
  crack_delta_mm10: number;
  lat_e7: number;       // signed fixed-point ×1e7
  lon_e7: number;       // signed fixed-point ×1e7
  battery_mv: number;
}

// Encode to a Uint8Array. Layout matches what the firmware puts on the wire.
export function encodePayload(r: DecodedReading): Uint8Array {
  const buf = new Uint8Array(20);
  const dv = new DataView(buf.buffer);
  buf[0] = r.severity & 0xff;
  buf[1] = r.sensor_mask & 0xff;
  dv.setUint16(2, r.rain_tips_15m & 0xffff, true);
  dv.setUint16(4, r.accel_rms_mg & 0xffff, true);
  dv.setInt16(6, r.tilt_delta_ddeg, true);
  dv.setInt16(8, r.crack_delta_mm10, true);
  dv.setInt32(10, r.lat_e7 | 0, true);
  dv.setInt32(14, r.lon_e7 | 0, true);
  dv.setUint16(18, r.battery_mv & 0xffff, true);
  return buf;
}

export function decodePayload(buf: Uint8Array): DecodedReading {
  if (buf.length < 20) {
    throw new Error(`payload too short: ${buf.length} bytes (expected 20)`);
  }
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  return {
    severity: buf[0] as Severity,
    sensor_mask: buf[1],
    rain_tips_15m: dv.getUint16(2, true),
    accel_rms_mg: dv.getUint16(4, true),
    tilt_delta_ddeg: dv.getInt16(6, true),
    crack_delta_mm10: dv.getInt16(8, true),
    lat_e7: dv.getInt32(10, true),
    lon_e7: dv.getInt32(14, true),
    battery_mv: dv.getUint16(18, true),
  };
}

// base64 helpers (browser & node compatible)
export function bytesToBase64(bytes: Uint8Array): string {
  if (typeof Buffer !== 'undefined') return Buffer.from(bytes).toString('base64');
  let s = '';
  for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]!);
  return btoa(s);
}

// Battery helpers — LiSOCl2 single cell: 3.0V = 0%, 3.6V = 100%.
export const BATTERY_MIN_MV = 3000;
export const BATTERY_MAX_MV = 3600;

export function batteryPercent(mv: number | null | undefined): number | null {
  if (mv == null) return null;
  if (mv >= BATTERY_MAX_MV) return 100;
  if (mv <= BATTERY_MIN_MV) return 0;
  return Math.round(((mv - BATTERY_MIN_MV) / (BATTERY_MAX_MV - BATTERY_MIN_MV)) * 100);
}

export function base64ToBytes(b64: string): Uint8Array {
  if (typeof Buffer !== 'undefined') return new Uint8Array(Buffer.from(b64, 'base64'));
  const s = atob(b64);
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
}
