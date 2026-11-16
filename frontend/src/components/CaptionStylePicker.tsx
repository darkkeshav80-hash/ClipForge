import React, { useState, useEffect, useRef } from 'react';
import { 
  Check, 
  Sparkles, 
  Flame, 
  Gamepad2, 
  Type, 
  ChevronLeft, 
  ChevronRight, 
  Search, 
  Eye, 
  ShieldCheck, 
  Play, 
  Pause,
  Video,
  Monitor
} from 'lucide-react';
import { CaptionStyleConfig } from '../types';
import { INITIAL_PRESETS } from '../types/presets';

const STORAGE_KEY = 'clipforge_selected_caption_style';
const SAMPLE_WORDS = ['VIRAL', 'HOOKS', 'THAT', 'EXPLODE'];

interface CaptionStylePickerProps {
  presets?: CaptionStyleConfig[];
  selectedPresetId?: string;
  onSelectPreset: (presetId: string) => void;
  className?: string;
}

/**
 * Computes high-contrast, non-choking CSS styles for any preset.
 * Avoids browser -webkit-text-stroke inward glyph occlusion, ensuring 100% bright,
 * crisp, authentic subtitle rendering that mirrors FFmpeg libass export.
 */
export const getPresetComputedStyle = (
  preset: CaptionStyleConfig,
  isWordActive: boolean,
  isCompactCard: boolean = false
): React.CSSProperties => {
  const pId = (preset.preset_id || '').toLowerCase();
  const fontFam = preset.font_family || 'Impact';
  const textColor = preset.text_color || '#FFFFFF';
  const hlColor = preset.highlight_color || '#FACC15';
  const strokeColor = preset.outline_color || '#000000';

  // 1. NEON / CYBER GLOW STYLES
  if (pId.includes('neon') || pId.includes('rgb')) {
    const activeColor = hlColor || '#FF3DF2';
    const baseColor = textColor === '#FFFFFF' ? '#00FFFF' : textColor;
    const currentColor = isWordActive ? activeColor : baseColor;
    return {
      fontFamily: fontFam,
      color: '#FFFFFF',
      backgroundColor: 'transparent',
      textShadow: isWordActive
        ? `0 0 6px ${currentColor}, 0 0 14px ${currentColor}, 0 0 24px ${currentColor}, 1px 1px 1px #000`
        : `0 0 4px ${currentColor}, 0 0 10px ${currentColor}, 1px 1px 1px #000`,
      filter: isWordActive ? `drop-shadow(0 0 8px ${currentColor})` : `drop-shadow(0 0 4px ${currentColor})`,
    };
  }

  // 2. BOXED / BADGE STYLES
  if (pId.includes('box')) {
    return {
      fontFamily: fontFam,
      color: isWordActive ? hlColor : textColor,
      backgroundColor: isWordActive ? 'rgba(0, 0, 0, 0.95)' : 'rgba(15, 23, 42, 0.85)',
      border: isWordActive ? `1.5px solid ${hlColor}` : '1.5px solid rgba(255, 255, 255, 0.2)',
      padding: isCompactCard ? '1px 4px' : '2px 8px',
      borderRadius: isCompactCard ? '3px' : '6px',
      textShadow: '0 1px 2px rgba(0,0,0,0.9)',
      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.85))',
    };
  }

  // 3. HIGHLIGHTER / MARKER SWEEP STYLES
  if (pId.includes('marker') || pId.includes('highlighter')) {
    if (isWordActive) {
      return {
        fontFamily: fontFam,
        color: '#000000',
        backgroundColor: hlColor || '#FFE600',
        padding: isCompactCard ? '1px 5px' : '2px 9px',
        borderRadius: isCompactCard ? '3px' : '5px',
        textShadow: 'none',
        fontWeight: '900',
        filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.9))',
      };
    }
    return {
      fontFamily: fontFam,
      color: textColor || '#FFFFFF',
      backgroundColor: 'transparent',
      textShadow: '0 0 2px #000, 1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000',
      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.9))',
    };
  }

  // 4. FIRE / LAVA STYLES
  if (pId.includes('fire')) {
    const fireColor = isWordActive ? '#FF7A00' : '#FFFFFF';
    return {
      fontFamily: fontFam,
      color: fireColor,
      backgroundColor: 'transparent',
      textShadow: isWordActive
        ? '0 0 6px #FF4500, 0 0 14px #FF0000, 1px 1px 0 #000, -1px -1px 0 #000'
        : '0 0 3px #FF7A00, 1px 1px 0 #000',
      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.9))',
    };
  }

  // 5. COMIC POP STYLES
  if (pId.includes('comic')) {
    return {
      fontFamily: fontFam,
      color: isWordActive ? '#FFFFFF' : (textColor || '#FFE600'),
      backgroundColor: 'transparent',
      textShadow: isCompactCard
        ? '1px 1px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1.5px 2px 0 #000'
        : '2px 2px 0 #000, -1.5px -1.5px 0 #000, 1.5px -1.5px 0 #000, -1.5px 1.5px 0 #000, 3px 3px 0 #000',
      filter: 'drop-shadow(0 3px 3px rgba(0,0,0,0.95))',
    };
  }

  // 6. MINIMAL / CLEAN WHITE / PODCAST
  if (pId.includes('clean') || pId.includes('minimal')) {
    return {
      fontFamily: fontFam,
      color: isWordActive ? (hlColor || '#38BDF8') : (textColor || '#FFFFFF'),
      backgroundColor: pId.includes('podcast') ? 'rgba(15, 23, 42, 0.75)' : 'transparent',
      padding: pId.includes('podcast') ? (isCompactCard ? '1px 4px' : '2px 6px') : '0',
      borderRadius: '4px',
      textShadow: '0 1px 4px rgba(0,0,0,0.9), 0 0 2px rgba(0,0,0,0.8)',
      filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.85))',
    };
  }

  // 7. DEFAULT VIRAL / MRBEAST / HORMOZI / GAMING / GENERAL
  // Outward crisp boundary: Uses true multi-angle outer shadow that never bleeds inward
  const shadowDist = isCompactCard ? 1.2 : 2.0;
  const shadowStr = `
    0 0 2px ${strokeColor},
    ${shadowDist}px ${shadowDist}px 0 ${strokeColor},
    -${shadowDist}px -${shadowDist}px 0 ${strokeColor},
    ${shadowDist}px -${shadowDist}px 0 ${strokeColor},
    -${shadowDist}px ${shadowDist}px 0 ${strokeColor},
    0 2px 5px rgba(0,0,0,0.9)
  `;

  return {
    fontFamily: fontFam,
    color: isWordActive ? hlColor : textColor,
    backgroundColor: 'transparent',
    textShadow: shadowStr,
    filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.95))',
  };
};

export const CaptionStylePicker: React.FC<CaptionStylePickerProps> = ({
  presets = INITIAL_PRESETS,
  selectedPresetId,
  onSelectPreset,
  className = '',
}) => {
  // Use all available presets or fall back to INITIAL_PRESETS
  const activePresets = presets.length > 0 ? presets : INITIAL_PRESETS;

  // Selected preset state (default to saved in localStorage, or prop, or 'mrbeast')
  const [currentId, setCurrentId] = useState<string>(() => {
    if (selectedPresetId) return selectedPresetId;
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && activePresets.some((p) => p.preset_id === saved)) {
      return saved;
    }
    return 'mrbeast';
  });

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeWordIdx, setActiveWordIdx] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [showSafeZones, setShowSafeZones] = useState<boolean>(true);
  const [backdropMode, setBackdropMode] = useState<'video' | 'dark'>('video');

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Sync external selectedPresetId if provided
  useEffect(() => {
    if (selectedPresetId && selectedPresetId !== currentId) {
      setCurrentId(selectedPresetId);
    }
  }, [selectedPresetId]);

  // Save selected preset to localStorage and notify parent
  const handleSelect = (id: string) => {
    setCurrentId(id);
    localStorage.setItem(STORAGE_KEY, id);
    onSelectPreset(id);
  };

  // Word-by-word animation loop for live sample preview
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setActiveWordIdx((prev) => (prev + 1) % SAMPLE_WORDS.length);
    }, 480);
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Active preset object
  const currentPreset =
    activePresets.find((p) => p.preset_id === currentId) ||
    activePresets[0] ||
    INITIAL_PRESETS[0];

  // Filter presets by category and search
  const filteredPresets = activePresets.filter((p) => {
    const matchesCat =
      selectedCategory === 'all' ||
      p.category?.toLowerCase() === selectedCategory.toLowerCase() ||
      (selectedCategory === 'recommended' && (p.is_recommended || p.preset_id.includes('beast') || p.preset_id.includes('hormozi')));
    const matchesSearch =
      !searchQuery ||
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      p.preset_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  // Scroll controls for CapCut-style horizontal row
  const scrollLeft = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: -320, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: 320, behavior: 'smooth' });
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with Search and Category Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <label className="block text-xs font-semibold text-slate-200 uppercase tracking-wide flex items-center space-x-2">
            <Type className="w-4 h-4 text-purple-400" />
            <span>Select Caption Style (Before Processing)</span>
          </label>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Choose a viral subtitle aesthetic. All clips generated for this project will render with this style.
          </p>
        </div>

        {/* Search bar */}
        <div className="relative w-full sm:w-60">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search styles (e.g. Beast, Neon)..."
            className="w-full pl-9 pr-3 py-1.5 rounded-xl glass-input text-xs text-white placeholder-slate-500 focus:ring-1 focus:ring-purple-500"
          />
        </div>
      </div>

      {/* Category Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs">
        {[
          { id: 'all', label: 'All Styles' },
          { id: 'recommended', label: 'Recommended', icon: Sparkles },
          { id: 'viral', label: 'Viral / Hooks', icon: Flame },
          { id: 'social', label: 'Social & Creators' },
          { id: 'gaming', label: 'Gaming & High Energy', icon: Gamepad2 },
          { id: 'minimal', label: 'Minimal / Clean' },
        ].map((cat) => {
          const Icon = cat.icon;
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all flex items-center space-x-1.5 ${
                isActive
                  ? 'bg-purple-600 text-white shadow-[0_0_12px_rgba(168,85,247,0.4)]'
                  : 'bg-white/[0.04] text-slate-400 hover:text-white hover:bg-white/[0.08]'
              }`}
            >
              {Icon && <Icon className="w-3 h-3" />}
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* CapCut-Style Horizontal Scrollable Style Row */}
      <div className="relative group">
        {/* Left Arrow Button */}
        <button
          type="button"
          onClick={scrollLeft}
          className="absolute -left-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/90 border border-white/20 text-white flex items-center justify-center shadow-lg hover:bg-purple-600 transition-all opacity-80 group-hover:opacity-100"
          aria-label="Scroll left"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Scrollable Container */}
        <div
          ref={scrollContainerRef}
          className="flex space-x-4 overflow-x-auto pb-3 pt-1 px-1 scrollbar-thin scrollbar-thumb-purple-600/30 scrollbar-track-transparent snap-x"
        >
          {filteredPresets.map((preset) => {
            const isSelected = preset.preset_id === currentId;
            const fontFam = preset.font_family || 'Impact';
            const hlColor = preset.highlight_color || '#FACC15';

            return (
              <div
                key={preset.preset_id}
                onClick={() => handleSelect(preset.preset_id)}
                className="flex flex-col items-center shrink-0 w-44 cursor-pointer select-none snap-start"
              >
                {/* Visual Card */}
                <div
                  className={`w-full h-24 rounded-2xl p-2.5 flex flex-col justify-between relative transition-all duration-200 overflow-hidden ${
                    isSelected
                      ? 'border-2 border-purple-400 bg-purple-500/20 shadow-[0_0_22px_rgba(168,85,247,0.45)] ring-2 ring-purple-500/40 scale-[1.02]'
                      : 'border border-white/[0.08] bg-slate-900/90 hover:border-white/[0.25] hover:bg-slate-800/90'
                  }`}
                >
                  {/* Selected Badge */}
                  {isSelected && (
                    <div className="absolute top-2 right-2 z-10 flex items-center space-x-0.5 px-2 py-0.5 rounded-full bg-purple-600 text-[10px] font-bold text-white shadow-md">
                      <Check className="w-3 h-3 stroke-[3]" />
                      <span>Selected</span>
                    </div>
                  )}

                  {/* Category Pill on Card */}
                  <div className="flex items-center space-x-1 text-[9px] uppercase font-mono tracking-wider text-slate-400">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: hlColor }}></span>
                    <span className="truncate max-w-[70px]">{preset.category || 'Viral'}</span>
                  </div>

                  {/* Sample Animated Sentence in Card - High Contrast & Crisp */}
                  <div className="flex items-center justify-center my-auto px-1 text-center">
                    <div
                      className="text-xs font-black tracking-tight leading-tight transition-transform flex flex-wrap justify-center gap-1"
                      style={{
                        textTransform: preset.all_caps ? 'uppercase' : 'none',
                      }}
                    >
                      {SAMPLE_WORDS.slice(0, 3).map((w, idx) => {
                        const isWordActive = idx === (activeWordIdx % 3);
                        const wordStyle = getPresetComputedStyle(preset, isWordActive, true);

                        return (
                          <span
                            key={idx}
                            style={wordStyle}
                            className={`inline-block transition-all duration-150 ${
                              isWordActive ? 'scale-110 font-black' : 'opacity-95'
                            }`}
                          >
                            {w}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {/* Bottom indicator bar */}
                  <div className="flex items-center justify-between text-[9px] font-mono text-slate-400 border-t border-white/[0.05] pt-1">
                    <span className="truncate max-w-[100px]">{fontFam}</span>
                    <span className="text-purple-400 font-bold">Bottom</span>
                  </div>
                </div>

                {/* Style Name under Card */}
                <span
                  className={`text-xs mt-2 font-semibold text-center truncate max-w-full transition-colors ${
                    isSelected ? 'text-purple-300 font-bold' : 'text-slate-300'
                  }`}
                >
                  {preset.name}
                </span>
              </div>
            );
          })}
        </div>

        {/* Right Arrow Button */}
        <button
          type="button"
          onClick={scrollRight}
          className="absolute -right-3 top-1/2 -translate-y-1/2 z-20 w-8 h-8 rounded-full bg-slate-900/90 border border-white/20 text-white flex items-center justify-center shadow-lg hover:bg-purple-600 transition-all opacity-80 group-hover:opacity-100"
          aria-label="Scroll right"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* 9:16 Phone-Shaped Export Preview (Bottom Position • Exact Subtitle Rules) */}
      <div className="rounded-3xl border border-white/[0.1] bg-slate-900/40 p-5 backdrop-blur-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <Eye className="w-4 h-4 text-purple-400" />
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">
              Real-Time 9:16 Mobile Preview (Exact ASS Subtitle Export)
            </h4>
          </div>

          <div className="flex items-center space-x-2.5 flex-wrap">
            {/* Backdrop Switcher (Real Video vs Dark Studio) */}
            <button
              type="button"
              onClick={() => setBackdropMode(backdropMode === 'video' ? 'dark' : 'video')}
              className={`text-[11px] px-2.5 py-1 rounded-lg border font-medium flex items-center space-x-1.5 transition-colors ${
                backdropMode === 'video'
                  ? 'bg-purple-600/20 text-purple-300 border-purple-500/40'
                  : 'bg-white/[0.04] text-slate-400 border-white/[0.08]'
              }`}
            >
              {backdropMode === 'video' ? <Video className="w-3.5 h-3.5 text-purple-400" /> : <Monitor className="w-3.5 h-3.5 text-slate-400" />}
              <span>Backdrop: {backdropMode === 'video' ? 'Creator Video' : 'Dark Studio'}</span>
            </button>

            {/* Safe Zones Toggle */}
            <button
              type="button"
              onClick={() => setShowSafeZones(!showSafeZones)}
              className={`text-[11px] px-2.5 py-1 rounded-lg border font-medium flex items-center space-x-1.5 transition-colors ${
                showSafeZones
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                  : 'bg-white/[0.04] text-slate-400 border-white/[0.08]'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Safe Zones {showSafeZones ? 'ON' : 'OFF'}</span>
            </button>

            {/* Play / Pause Animation Loop */}
            <button
              type="button"
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] text-slate-300 transition-colors"
              title={isPlaying ? 'Pause Animation' : 'Play Animation'}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Phone Frame Mockup */}
        <div className="relative mx-auto w-full max-w-[280px] sm:max-w-[310px] aspect-[9/16] rounded-[38px] border-[6px] border-slate-700/80 bg-slate-950 shadow-2xl overflow-hidden flex flex-col justify-between select-none">
          {/* Top Notch / Dynamic Island */}
          <div className="w-24 h-4 bg-black/90 rounded-full mx-auto mt-2.5 z-30 shadow-md border border-white/[0.05]"></div>

          {/* Realistic Video Backdrop or Dark Studio Visual */}
          {backdropMode === 'video' ? (
            <div className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden">
              <video
                src="/storage/previews/orig_04d1ddae855e.mp4"
                autoPlay
                loop
                muted
                playsInline
                className="w-full h-full object-cover scale-105"
              />
              {/* Cinematic Vignette Gradient over video */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/25 to-black/35 pointer-events-none"></div>
            </div>
          ) : (
            <div className="absolute inset-0 bg-gradient-to-b from-slate-950 via-[#0B0F1E] to-black">
              <div className="absolute inset-0 bg-radial-at-c from-purple-900/15 via-transparent to-transparent opacity-60"></div>
            </div>
          )}

          {/* Safe Zone Overlays (Shorts/TikTok/Reels UI) */}
          {showSafeZones && (
            <>
              {/* Top UI Safe Zone (15%) */}
              <div className="absolute top-0 left-0 right-0 h-[15%] border-b border-dashed border-red-500/40 bg-red-500/[0.04] flex items-center justify-center pointer-events-none z-10">
                <span className="text-[9px] font-mono font-bold text-red-400/80 uppercase tracking-wider drop-shadow-sm">
                  Top UI Safe Zone (15%)
                </span>
              </div>

              {/* Right Side UI Buttons Zone */}
              <div className="absolute top-[30%] right-0 bottom-[22%] w-12 border-l border-dashed border-red-500/40 bg-red-500/[0.04] flex items-center justify-center pointer-events-none z-10">
                <span className="text-[8px] font-mono font-bold text-red-400/80 [writing-mode:vertical-lr] uppercase tracking-wider drop-shadow-sm">
                  Action Icons
                </span>
              </div>

              {/* Bottom UI Controls Zone (Shorts/Reels description & sound bar - 20%) */}
              <div className="absolute bottom-0 left-0 right-0 h-[20%] border-t border-dashed border-red-500/40 bg-red-500/[0.04] flex items-center justify-center pointer-events-none z-10">
                <span className="text-[9px] font-mono font-bold text-red-400/80 uppercase tracking-wider drop-shadow-sm">
                  Bottom Controls Zone (20%)
                </span>
              </div>
            </>
          )}

          {/* CAPTIONS ONLY: EXACT BOTTOM POSITIONING (22% UP FROM BOTTOM, MAX 80% WIDTH, CENTERED) */}
          <div
            className="absolute left-1/2 -translate-x-1/2 w-[82%] max-w-[82%] text-center z-20 transition-all duration-200"
            style={{
              bottom: '22%', // Exactly 22% up from frame bottom: clears TikTok/Shorts UI
            }}
          >
            {/* Render the active word group according to preset settings */}
            <div
              className="flex flex-wrap items-center justify-center gap-1.5 leading-snug"
              style={{
                textTransform: currentPreset.all_caps ? 'uppercase' : 'none',
              }}
            >
              {SAMPLE_WORDS.map((word, idx) => {
                const isWordActive = idx === activeWordIdx;
                const wordStyle = getPresetComputedStyle(currentPreset, isWordActive, false);

                return (
                  <span
                    key={idx}
                    style={{
                      ...wordStyle,
                      fontSize: '23px',
                      fontWeight: currentPreset.font_weight || '900',
                    }}
                    className={`inline-block transition-all duration-150 ${
                      isWordActive ? 'scale-110 font-black z-10' : 'scale-100 opacity-95'
                    }`}
                  >
                    {word}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Bottom Live Info Pill inside Phone Mockup */}
          <div className="z-20 text-center pb-3">
            <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-black/85 backdrop-blur-md border border-white/10 text-[9px] font-mono text-slate-300 shadow-md">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Bottom 22% Baseline • Non-Overlapping ASS</span>
            </span>
          </div>
        </div>

        {/* Selected Preset Details Footer */}
        <div className="flex flex-wrap items-center justify-between text-xs text-slate-400 pt-1 border-t border-white/[0.06] font-mono">
          <div>
            Active Style: <span className="text-white font-bold">{currentPreset.name}</span> ({currentPreset.preset_id})
          </div>
          <div className="flex items-center space-x-3 text-[11px]">
            <span>Font: <strong className="text-slate-200">{currentPreset.font_family}</strong></span>
            <span>Position: <strong className="text-emerald-400">Bottom (22% up)</strong></span>
            <span>Outline: <strong className="text-slate-200">{currentPreset.outline_width}px</strong></span>
            <span>Max Width: <strong className="text-purple-300">80%</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
