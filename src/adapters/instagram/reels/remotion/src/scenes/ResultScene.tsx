import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

export const ResultScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const grade = (visual.grade as string) ?? "?/?";
  const feedback = (visual.feedback as string) ?? "";

  const bounceScale = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 200, mass: 0.8 },
  });

  const feedbackOpacity = interpolate(frame, [fps * 0.5, fps * 0.8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const parts = grade.split("/");
  const awarded = parseFloat(parts[0] ?? "0");
  const max = parseFloat(parts[1] ?? "100");
  const pct = max > 0 ? awarded / max : 0;

  let gradeColor = "#ff6b6b";
  if (pct >= 0.9) gradeColor = "#51cf66";
  else if (pct >= 0.7) gradeColor = "#ffd43b";
  else if (pct >= 0.5) gradeColor = "#ff922b";

  return (
    <AbsoluteFill
      style={{
        background: "radial-gradient(ellipse at center, #1a1a3e, #0f0c29)",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          transform: `scale(${bounceScale})`,
          color: gradeColor,
          fontSize: 120,
          fontWeight: 900,
          fontFamily: "system-ui, sans-serif",
          textShadow: `0 0 60px ${gradeColor}40`,
          marginBottom: 30,
        }}
      >
        {grade}
      </div>
      <div
        style={{
          opacity: feedbackOpacity,
          color: "rgba(255,255,255,0.85)",
          fontSize: 28,
          fontWeight: 500,
          fontFamily: "system-ui, sans-serif",
          textAlign: "center",
          maxWidth: "80%",
          lineHeight: 1.5,
        }}
      >
        {feedback}
      </div>
    </AbsoluteFill>
  );
};
