import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { rhythm, typography } from "./tokens";
import { clamp, easeOutCubic } from "./math";

export type CaptionCue = { text: string; start: number; end: number };

/**
 * Split a line into caption chunks of 1-3 words and distribute time by
 * character weight, the way the reference captions read (2-3 words per beat).
 */
export const buildCues = (line: string, startFrame: number, endFrame: number): CaptionCue[] => {
  const words = line.trim().split(/\s+/).filter(Boolean);
  const chunks: string[][] = [];
  for (let i = 0; i < words.length; i += rhythm.captionWordsPerChunk) {
    chunks.push(words.slice(i, i + rhythm.captionWordsPerChunk));
  }
  const totalChars = Math.max(1, words.join("").length);
  let cursor = startFrame;
  const span = endFrame - startFrame;
  return chunks.map((chunk) => {
    const weight = chunk.join("").length / totalChars;
    const dur = Math.max(8, Math.round(span * weight));
    const cue = {
      text: chunk.join(" "),
      start: Math.round(cursor),
      end: Math.round(Math.min(endFrame, cursor + dur)),
    };
    cursor += dur;
    return cue;
  });
};

export const Captions: React.FC<{ cues: CaptionCue[]; y?: number }> = ({ cues, y = rhythm.captionY }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const active = cues.find((c) => frame >= c.start && frame < c.end);
  if (!active) return null;

  const local = frame - active.start;
  const entrance = easeOutCubic(clamp(local / Math.max(1, fps * 0.18)));
  const exit = clamp((active.end - frame) / Math.max(1, fps * 0.1));

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: height * y,
        display: "flex",
        justifyContent: "center",
        padding: `0 ${width * 0.08}px`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily: typography.captionFamily,
          fontWeight: 900,
          fontSize: typography.captionSize * (width / 1080),
          lineHeight: 1.16,
          letterSpacing: 0.2,
          color: "#fdf6ea",
          textAlign: "center",
          textShadow: [
            `0 0 ${typography.captionStroke}px rgba(16,10,22,0.92)`,
            `0 ${4}px ${10}px rgba(16,10,22,0.8)`,
            "0 1px 0 rgba(16,10,22,1)",
          ].join(", "),
          WebkitTextStroke: `${2.2 * (width / 1080)}px rgba(16,10,22,0.85)`,
          transform: `translateY(${interpolate(entrance, [0, 1], [12, 0])}px) scale(${0.97 + entrance * 0.03})`,
          opacity: Math.min(entrance * 1.6, exit),
        }}
      >
        {active.text}
      </div>
    </div>
  );
};
