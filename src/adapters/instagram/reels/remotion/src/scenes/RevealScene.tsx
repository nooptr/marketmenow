import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { VisualProps } from "../schema";

export const RevealScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const rawImage = (visual.image as string) ?? "";
  const imageSrc = rawImage ? staticFile(rawImage) : "";

  const slideIn = spring({
    frame,
    fps,
    config: {
      damping: Number(visual.spring_damping ?? 12),
      stiffness: Number(visual.spring_stiffness ?? 100),
    },
  });
  const translateY = interpolate(slideIn, [0, 1], [800, 0]);

  return (
    <AbsoluteFill
      style={{
        background: (visual.background as string) ?? "#000000",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {imageSrc && (
        <Img
          src={imageSrc}
          style={{
            maxWidth: "85%",
            maxHeight: "80%",
            objectFit: "contain",
            borderRadius: Number(visual.border_radius ?? 16),
            transform: `translateY(${translateY}px)`,
            boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          }}
        />
      )}
    </AbsoluteFill>
  );
};
