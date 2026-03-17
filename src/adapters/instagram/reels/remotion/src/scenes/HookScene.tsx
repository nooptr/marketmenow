import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

export const HookScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const text = (visual.text_overlay as string) ?? "";
  const opacity = interpolate(frame, [0, fps * 0.3], [0, 1], {
    extrapolateRight: "clamp",
  });
  const scale = interpolate(frame, [0, fps * 0.4], [0.6, 1], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: (visual.background as string) ?? "linear-gradient(135deg, #0f0c29, #302b63, #24243e)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          color: (visual.text_color as string) ?? "#fff",
          fontSize: Number(visual.font_size ?? 52),
          fontWeight: Number(visual.font_weight ?? 800),
          textAlign: "center",
          padding: (visual.padding as string) ?? "0 60px",
          fontFamily: (visual.font_family as string) ?? "system-ui, sans-serif",
          textShadow: (visual.text_shadow as string) ?? "0 4px 30px rgba(0,0,0,0.5)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};
