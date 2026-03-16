import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

export const TransitionScene: React.FC<{ visual: VisualProps }> = ({
  visual,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const imageSrc = (visual.image as string) ?? "";

  const progress = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
  });

  const translateX = interpolate(progress, [0, 0.6, 1], [0, -50, -400]);
  const scale = interpolate(progress, [0, 0.6, 1], [1, 0.7, 0.4]);
  const platformOpacity = interpolate(progress, [0.3, 0.7], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ background: "#16213e" }}>
      {imageSrc && (
        <Img
          src={imageSrc}
          style={{
            position: "absolute",
            top: "15%",
            left: "50%",
            maxWidth: "70%",
            maxHeight: "60%",
            objectFit: "contain",
            borderRadius: 12,
            transform: `translateX(calc(-50% + ${translateX}px)) scale(${scale})`,
          }}
        />
      )}
      <div
        style={{
          position: "absolute",
          right: "5%",
          top: "20%",
          width: "45%",
          height: "60%",
          opacity: platformOpacity,
          background: "linear-gradient(145deg, #667eea, #764ba2)",
          borderRadius: 20,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          padding: 30,
          boxShadow: "0 20px 60px rgba(118,75,162,0.4)",
        }}
      >
        <div
          style={{
            color: "#fff",
            fontSize: 28,
            fontWeight: 700,
            fontFamily: "system-ui, sans-serif",
            marginBottom: 16,
          }}
        >
          Wayground AI
        </div>
        <div
          style={{
            color: "rgba(255,255,255,0.8)",
            fontSize: 18,
            fontFamily: "system-ui, sans-serif",
            textAlign: "center",
          }}
        >
          Grading in progress...
        </div>
      </div>
    </AbsoluteFill>
  );
};
