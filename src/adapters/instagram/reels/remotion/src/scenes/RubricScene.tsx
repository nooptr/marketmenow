import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

interface RubricItem {
  name: string;
  description: string;
  max_points: number;
}

export const RubricScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  let rubricItems: RubricItem[] = [];
  const rawItems = visual.rubric_items;
  if (typeof rawItems === "string") {
    try {
      rubricItems = JSON.parse(rawItems);
    } catch {}
  } else if (Array.isArray(rawItems)) {
    rubricItems = rawItems as RubricItem[];
  }

  const staggerDelay = Math.floor(fps * 0.4);

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(180deg, #0f0c29, #1a1a3e)",
        padding: "60px 40px",
        flexDirection: "column",
        justifyContent: "flex-start",
      }}
    >
      <div
        style={{
          color: "#667eea",
          fontSize: 32,
          fontWeight: 800,
          fontFamily: "system-ui, sans-serif",
          marginBottom: 30,
          textTransform: "uppercase",
          letterSpacing: 2,
        }}
      >
        Rubric
      </div>
      {rubricItems.map((item, idx) => {
        const itemProgress = spring({
          frame: frame - idx * staggerDelay,
          fps,
          config: { damping: 12, stiffness: 120 },
        });

        const translateX = interpolate(itemProgress, [0, 1], [300, 0]);
        const opacity = interpolate(itemProgress, [0, 1], [0, 1]);

        return (
          <div
            key={item.name}
            style={{
              opacity,
              transform: `translateX(${translateX}px)`,
              background: "rgba(255,255,255,0.08)",
              borderRadius: 14,
              padding: "18px 24px",
              marginBottom: 14,
              borderLeft: "4px solid #667eea",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span
                style={{
                  color: "#fff",
                  fontSize: 22,
                  fontWeight: 700,
                  fontFamily: "system-ui, sans-serif",
                }}
              >
                {item.name}
              </span>
              <span
                style={{
                  color: "#667eea",
                  fontSize: 20,
                  fontWeight: 600,
                  fontFamily: "system-ui, sans-serif",
                }}
              >
                {item.max_points} pts
              </span>
            </div>
            <div
              style={{
                color: "rgba(255,255,255,0.6)",
                fontSize: 16,
                fontFamily: "system-ui, sans-serif",
                marginTop: 6,
              }}
            >
              {item.description}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
