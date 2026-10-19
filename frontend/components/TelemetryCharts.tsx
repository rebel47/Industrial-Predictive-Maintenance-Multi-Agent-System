'use client';

import React, { useState } from 'react';
import { TelemetryResponse } from '../lib/types';
import { Activity, Thermometer, Gauge, Zap, RefreshCw } from 'lucide-react';

interface TelemetryChartsProps {
  data: TelemetryResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({
  data,
  loading,
  onRefresh,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<{ x: number; y: number; val: number; label: string } | null>(null);

  if (!data || !data.telemetry || data.telemetry.length === 0) {
    return (
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <Activity className="w-8 h-8 mx-auto mb-2 opacity-50 animate-pulse" />
        <p>Loading asset telemetry stream...</p>
      </div>
    );
  }

  const { telemetry, spectrum, characteristic_frequencies, thresholds } = data;
  const latest = telemetry[telemetry.length - 1];

  // Helper for SVG line generation
  const buildSvgPath = (
    values: number[],
    minVal: number,
    maxVal: number,
    width: number,
    height: number,
    padding = 20
  ) => {
    if (values.length < 2) return '';
    const innerW = width - padding * 2;
    const innerH = height - padding * 2;
    const range = maxVal - minVal || 1;

    const points = values.map((v, i) => {
      const x = padding + (i / (values.length - 1)) * innerW;
      const y = height - padding - ((v - minVal) / range) * innerH;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });

    return `M ${points.join(' L ')}`;
  };

  // Telemetry limits
  const vibValues = telemetry.map((t) => t.vibration_rms);
  const minVib = 0;
  const maxVib = Math.max(6.0, ...vibValues);

  const tempValues = telemetry.map((t) => t.temperature);
  const minTemp = Math.min(50, ...tempValues);
  const maxTemp = Math.max(90, ...tempValues);

  // FFT limits
  const specFreqs = spectrum.map((s) => s.freq);
  const specAmps = spectrum.map((s) => s.amp);
  const maxAmp = Math.max(0.1, ...specAmps);

  const chartW = 540;
  const chartH = 180;
  const pad = 30;

  return (
    <div className="space-y-6">
      {/* Top Bar with Latest KPIs & Refresh */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900/50 border border-slate-800 p-4 rounded-xl">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full sm:w-auto">
          <div>
            <span className="text-[10px] text-slate-400 font-mono block">VIBRATION RMS</span>
            <span className={`text-base font-mono font-bold ${latest.vibration_rms > thresholds.vibration_trip ? 'text-rose-400' : latest.vibration_rms > thresholds.vibration_alert ? 'text-amber-400' : 'text-emerald-400'}`}>
              {latest.vibration_rms.toFixed(2)} mm/s
            </span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-mono block">BEARING TEMP</span>
            <span className={`text-base font-mono font-bold ${latest.temperature > thresholds.temp_trip ? 'text-rose-400' : latest.temperature > thresholds.temp_warning ? 'text-amber-400' : 'text-emerald-400'}`}>
              {latest.temperature.toFixed(1)} °C
            </span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-mono block">MOTOR CURRENT</span>
            <span className="text-base font-mono font-bold text-slate-200">
              {latest.motor_current.toFixed(1)} A
            </span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-mono block">DISCHARGE PRESS.</span>
            <span className="text-base font-mono font-bold text-slate-200">
              {latest.discharge_pressure_bar.toFixed(2)} bar
            </span>
          </div>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 text-xs font-medium px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition disabled:opacity-50 self-end sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh 60m Stream</span>
        </button>
      </div>

      {/* Grid of Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vibration Trend Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-rose-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                Vibration Velocity Trend (ISO 10816-3)
              </h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-amber-400">
                <span className="w-2.5 h-0.5 bg-amber-400 inline-block border-b border-dashed" /> Alert 2.8
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="w-2.5 h-0.5 bg-rose-400 inline-block border-b border-dashed" /> Trip 4.5
              </span>
            </div>
          </div>

          <div className="w-full overflow-hidden">
            <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-auto">
              {/* Grid lines */}
              <line x1={pad} y1={pad} x2={chartW - pad} y2={pad} stroke="#1e293b" strokeDasharray="3 3" />
              <line x1={pad} y1={chartH / 2} x2={chartW - pad} y2={chartH / 2} stroke="#1e293b" strokeDasharray="3 3" />
              <line x1={pad} y1={chartH - pad} x2={chartW - pad} y2={chartH - pad} stroke="#334155" />

              {/* Threshold Lines */}
              {(() => {
                const innerH = chartH - pad * 2;
                const range = maxVib - minVib;
                const alertY = chartH - pad - ((thresholds.vibration_alert - minVib) / range) * innerH;
                const tripY = chartH - pad - ((thresholds.vibration_trip - minVib) / range) * innerH;
                return (
                  <>
                    <line x1={pad} y1={alertY} x2={chartW - pad} y2={alertY} stroke="#f59e0b" strokeWidth="1" strokeDasharray="4 4" />
                    <line x1={pad} y1={tripY} x2={chartW - pad} y2={tripY} stroke="#ef4444" strokeWidth="1" strokeDasharray="4 4" />
                  </>
                );
              })()}

              {/* Data Path */}
              <path
                d={buildSvgPath(vibValues, minVib, maxVib, chartW, chartH, pad)}
                fill="none"
                stroke="#f43f5e"
                strokeWidth="2"
              />

              {/* End Point Dot */}
              {(() => {
                const innerW = chartW - pad * 2;
                const innerH = chartH - pad * 2;
                const lastY = chartH - pad - ((latest.vibration_rms - minVib) / (maxVib - minVib)) * innerH;
                return <circle cx={chartW - pad} cy={lastY} r="4" fill="#f43f5e" />;
              })()}

              {/* Y Axis Labels */}
              <text x={pad - 6} y={pad + 4} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                {maxVib.toFixed(1)}
              </text>
              <text x={pad - 6} y={chartH - pad} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                0.0
              </text>
              {/* X Axis Labels */}
              <text x={pad} y={chartH - 8} fill="#64748b" fontSize="9" textAnchor="start" fontFamily="monospace">
                -60 min
              </text>
              <text x={chartW - pad} y={chartH - 8} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                Now
              </text>
            </svg>
          </div>
        </div>

        {/* Temperature Trend Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Thermometer className="w-4 h-4 text-orange-400" />
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
                Bearing Housing Temperature (°C)
              </h3>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-mono">
              <span className="flex items-center gap-1 text-amber-400">
                <span className="w-2.5 h-0.5 bg-amber-400 inline-block border-b border-dashed" /> Warn 75°C
              </span>
              <span className="flex items-center gap-1 text-rose-400">
                <span className="w-2.5 h-0.5 bg-rose-400 inline-block border-b border-dashed" /> Trip 85°C
              </span>
            </div>
          </div>

          <div className="w-full overflow-hidden">
            <svg viewBox={`0 0 ${chartW} ${chartH}`} className="w-full h-auto">
              {/* Grid lines */}
              <line x1={pad} y1={pad} x2={chartW - pad} y2={pad} stroke="#1e293b" strokeDasharray="3 3" />
              <line x1={pad} y1={chartH / 2} x2={chartW - pad} y2={chartH / 2} stroke="#1e293b" strokeDasharray="3 3" />
              <line x1={pad} y1={chartH - pad} x2={chartW - pad} y2={chartH - pad} stroke="#334155" />

              {/* Threshold Lines */}
              {(() => {
                const innerH = chartH - pad * 2;
                const range = maxTemp - minTemp;
                const warnY = chartH - pad - ((thresholds.temp_warning - minTemp) / range) * innerH;
                const tripY = chartH - pad - ((thresholds.temp_trip - minTemp) / range) * innerH;
                return (
                  <>
                    <line x1={pad} y1={warnY} x2={chartW - pad} y2={warnY} stroke="#f59e0b" strokeWidth="1" strokeDasharray="4 4" />
                    <line x1={pad} y1={tripY} x2={chartW - pad} y2={tripY} stroke="#ef4444" strokeWidth="1" strokeDasharray="4 4" />
                  </>
                );
              })()}

              {/* Data Path */}
              <path
                d={buildSvgPath(tempValues, minTemp, maxTemp, chartW, chartH, pad)}
                fill="none"
                stroke="#fb923c"
                strokeWidth="2"
              />

              {/* End Point Dot */}
              {(() => {
                const innerW = chartW - pad * 2;
                const innerH = chartH - pad * 2;
                const lastY = chartH - pad - ((latest.temperature - minTemp) / (maxTemp - minTemp)) * innerH;
                return <circle cx={chartW - pad} cy={lastY} r="4" fill="#fb923c" />;
              })()}

              {/* Y Axis Labels */}
              <text x={pad - 6} y={pad + 4} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                {maxTemp.toFixed(0)}°C
              </text>
              <text x={pad - 6} y={chartH - pad} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                {minTemp.toFixed(0)}°C
              </text>
              {/* X Axis Labels */}
              <text x={pad} y={chartH - 8} fill="#64748b" fontSize="9" textAnchor="start" fontFamily="monospace">
                -60 min
              </text>
              <text x={chartW - pad} y={chartH - 8} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                Now
              </text>
            </svg>
          </div>
        </div>
      </div>

      {/* High-Resolution FFT Vibration Spectrum Chart */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <Gauge className="w-4 h-4 text-blue-400" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200 font-mono">
              High-Resolution Vibration Spectrum (FFT 0 - 500 Hz)
            </h3>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-[10px] font-mono">
            {characteristic_frequencies.map((cf) => (
              <span key={cf.label} className="flex items-center gap-1.5" style={{ color: cf.color }}>
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: cf.color }} />
                <span>{cf.label} ({cf.frequency} Hz)</span>
              </span>
            ))}
          </div>
        </div>

        <div className="w-full overflow-hidden">
          {(() => {
            const fftW = 1080;
            const fftH = 200;
            const fftPad = 35;
            const innerW = fftW - fftPad * 2;
            const innerH = fftH - fftPad * 2;
            const maxF = 500;

            const pathD = buildSvgPath(specAmps, 0, maxAmp, fftW, fftH, fftPad);

            return (
              <svg viewBox={`0 0 ${fftW} ${fftH}`} className="w-full h-auto">
                {/* Horizontal Grid */}
                <line x1={fftPad} y1={fftPad} x2={fftW - fftPad} y2={fftPad} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1={fftPad} y1={fftH / 2} x2={fftW - fftPad} y2={fftH / 2} stroke="#1e293b" strokeDasharray="3 3" />
                <line x1={fftPad} y1={fftH - fftPad} x2={fftW - fftPad} y2={fftH - fftPad} stroke="#334155" />

                {/* Characteristic frequency vertical marker lines */}
                {characteristic_frequencies.map((cf) => {
                  const x = fftPad + (cf.frequency / maxF) * innerW;
                  return (
                    <g key={cf.label}>
                      <line
                        x1={x}
                        y1={fftPad}
                        x2={x}
                        y2={fftH - fftPad}
                        stroke={cf.color}
                        strokeWidth="1.2"
                        strokeDasharray="4 2"
                      />
                      <text
                        x={x + 3}
                        y={fftPad + 12}
                        fill={cf.color}
                        fontSize="9"
                        fontFamily="monospace"
                        fontWeight="bold"
                      >
                        {cf.label.split(' ')[0]}
                      </text>
                    </g>
                  );
                })}

                {/* Spectrum Curve */}
                <path d={pathD} fill="none" stroke="#3b82f6" strokeWidth="1.5" />

                {/* Frequency Axis Markers */}
                {[0, 100, 200, 300, 400, 500].map((f) => {
                  const x = fftPad + (f / maxF) * innerW;
                  return (
                    <text
                      key={f}
                      x={x}
                      y={fftH - 12}
                      fill="#64748b"
                      fontSize="9"
                      textAnchor="middle"
                      fontFamily="monospace"
                    >
                      {f} Hz
                    </text>
                  );
                })}

                {/* Y Axis Top Label */}
                <text x={fftPad - 6} y={fftPad + 4} fill="#64748b" fontSize="9" textAnchor="end" fontFamily="monospace">
                  {maxAmp.toFixed(3)}g
                </text>
              </svg>
            );
          })()}
        </div>
      </div>
    </div>
  );
};
