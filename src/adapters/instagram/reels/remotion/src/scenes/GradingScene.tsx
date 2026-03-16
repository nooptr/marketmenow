import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

interface RubricEval {
  rubric_item_name: string;
  points_awarded: number;
  max_points: number;
  feedback: string;
}

interface GradingResultData {
  rubric_evaluations?: RubricEval[];
}

export const GradingScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  let evaluations: RubricEval[] = [];
  const rawResult = visual.grading_result;
  if (typeof rawResult === "string") {
    try {
      const parsed = JSON.parse(rawResult) as GradingResultData;
      evaluations = parsed.rubric_evaluations ?? [];
    } catch {}
  } else if (rawResult && typeof rawResult === "object") {
    evaluations =
      (rawResult as GradingResultData).rubric_evaluations ?? [];
  }

  const staggerDelay = Math.floor(fps * 0.5);

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
          color: "#4ecdc4",
          fontSize: 28,
          fontWeight: 800,
          fontFamily: "system-ui, sans-serif",
          marginBottom: 24,
          textTransform: "uppercase",
          letterSpacing: 2,
        }}
      >
        Grading...
      </div>
      {evaluations.map((ev, idx) => {
        const entryFrame = idx * staggerDelay;
        const progress = spring({
          frame: frame - entryFrame,
          fps,
          config: { damping: 14, stiffness: 100 },
        });

        const barWidth = interpolate(
          progress,
          [0, 1],
          [0, (ev.points_awarded / ev.max_points) * 100]
        );
        const opacity = interpolate(progress, [0, 0.3], [0, 1], {
          extrapolateRight: "clamp",
        });

        const checkOpacity = interpolate(
          frame - entryFrame,
          [fps * 0.6, fps * 0.8],
          [0, 1],
          { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
        );

        return (
          <div
            key={ev.rubric_item_name}
            style={{
              opacity,
              marginBottom: 16,
              background: "rgba(255,255,255,0.06)",
              borderRadius: 12,
              padding: "16px 20px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 8,
              }}
            >
              <span
                style={{
                  color: "#fff",
                  fontSize: 20,
                  fontWeight: 600,
                  fontFamily: "system-ui, sans-serif",
                }}
              >
                {ev.rubric_item_name}
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    color: "#4ecdc4",
                    fontSize: 20,
                    fontWeight: 700,
                    fontFamily: "system-ui, sans-serif",
                  }}
                >
                  {ev.points_awarded}/{ev.max_points}
                </span>
                <span style={{ opacity: checkOpacity, fontSize: 22 }}>
                  ✓
                </span>
              </div>
            </div>
            <div
              style={{
                height: 8,
                background: "rgba(255,255,255,0.1)",
                borderRadius: 4,
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  width: `${barWidth}%`,
                  height: "100%",
                  background: "linear-gradient(90deg, #667eea, #4ecdc4)",
                  borderRadius: 4,
                }}
              />
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
