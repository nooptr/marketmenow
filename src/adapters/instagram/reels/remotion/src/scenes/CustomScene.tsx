import React from "react";
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

interface AnimationConfig {
  type?: string;
  delay_frames?: number;
  damping?: number;
  stiffness?: number;
  mass?: number;
  duration_frames?: number;
}

interface LayerPosition {
  top?: string;
  bottom?: string;
  left?: string;
  right?: string;
  transform?: string;
}

interface LayerSize {
  width?: string;
  height?: string;
}

interface LayerStyle {
  font_size?: number;
  font_weight?: number;
  font_family?: string;
  color?: string;
  text_align?: string;
  line_height?: number;
  background?: string;
  border_radius?: number;
  padding?: string;
  text_shadow?: string;
  opacity?: number;
  [key: string]: unknown;
}

interface LayerDef {
  type: string;
  src?: string;
  content?: string;
  position?: LayerPosition;
  size?: LayerSize;
  style?: LayerStyle;
  border_radius?: number;
  animation?: AnimationConfig;
  object_fit?: string;
}

function resolveAnimation(
  anim: AnimationConfig | undefined,
  frame: number,
  fps: number,
): { opacity: number; transform: string } {
  if (!anim || !anim.type) {
    return { opacity: 1, transform: "none" };
  }

  const delay = anim.delay_frames ?? 0;
  const localFrame = Math.max(0, frame - delay);

  switch (anim.type) {
    case "fade": {
      const dur = anim.duration_frames ?? Math.round(fps * 0.3);
      const opacity = interpolate(localFrame, [0, dur], [0, 1], {
        extrapolateRight: "clamp",
      });
      return { opacity, transform: "none" };
    }
    case "spring": {
      const s = spring({
        frame: localFrame,
        fps,
        config: {
          damping: anim.damping ?? 12,
          stiffness: anim.stiffness ?? 100,
          mass: anim.mass ?? 1,
        },
      });
      const scale = interpolate(s, [0, 1], [0.8, 1]);
      const opacity = interpolate(s, [0, 1], [0, 1]);
      return { opacity, transform: `scale(${scale})` };
    }
    case "slide_up": {
      const s = spring({
        frame: localFrame,
        fps,
        config: {
          damping: anim.damping ?? 14,
          stiffness: anim.stiffness ?? 80,
        },
      });
      const y = interpolate(s, [0, 1], [120, 0]);
      return { opacity: 1, transform: `translateY(${y}px)` };
    }
    case "slide_down": {
      const s = spring({
        frame: localFrame,
        fps,
        config: {
          damping: anim.damping ?? 14,
          stiffness: anim.stiffness ?? 80,
        },
      });
      const y = interpolate(s, [0, 1], [-120, 0]);
      return { opacity: 1, transform: `translateY(${y}px)` };
    }
    case "scale": {
      const s = spring({
        frame: localFrame,
        fps,
        config: {
          damping: anim.damping ?? 10,
          stiffness: anim.stiffness ?? 150,
        },
      });
      return { opacity: 1, transform: `scale(${s})` };
    }
    default:
      return { opacity: 1, transform: "none" };
  }
}

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function styleFromDef(style: LayerStyle | undefined): React.CSSProperties {
  if (!style) return {};
  const css: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(style)) {
    css[snakeToCamel(key)] = val;
  }
  return css as React.CSSProperties;
}

function positionStyle(pos: LayerPosition | undefined): React.CSSProperties {
  if (!pos) return {};
  const css: Record<string, unknown> = {};
  if (pos.top != null) css.top = pos.top;
  if (pos.bottom != null) css.bottom = pos.bottom;
  if (pos.left != null) css.left = pos.left;
  if (pos.right != null) css.right = pos.right;
  if (pos.transform) css.transform = pos.transform;
  return css as React.CSSProperties;
}

function sizeStyle(size: LayerSize | undefined): React.CSSProperties {
  if (!size) return {};
  const css: Record<string, unknown> = {};
  if (size.width) css.width = size.width;
  if (size.height) css.height = size.height;
  return css as React.CSSProperties;
}

const Layer: React.FC<{ layer: LayerDef; frame: number; fps: number }> = ({
  layer,
  frame,
  fps,
}) => {
  const anim = resolveAnimation(layer.animation, frame, fps);

  const baseStyle: React.CSSProperties = {
    position: "absolute",
    ...positionStyle(layer.position),
    ...sizeStyle(layer.size),
    ...styleFromDef(layer.style),
    opacity: (layer.style?.opacity ?? 1) * anim.opacity,
    transform: [
      layer.position?.transform ?? "",
      anim.transform !== "none" ? anim.transform : "",
    ]
      .filter(Boolean)
      .join(" ") || undefined,
    borderRadius: layer.border_radius ?? layer.style?.border_radius,
  };

  switch (layer.type) {
    case "image": {
      const src = layer.src ? staticFile(layer.src) : "";
      if (!src) return null;
      return (
        <Img
          src={src}
          style={{
            ...baseStyle,
            objectFit: (layer.object_fit as React.CSSProperties["objectFit"]) ?? "contain",
          }}
        />
      );
    }
    case "text":
      return <div style={baseStyle}>{layer.content ?? ""}</div>;
    case "box":
      return <div style={baseStyle} />;
    default:
      return null;
  }
};

export const CustomScene: React.FC<{ visual: VisualProps }> = ({ visual }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const background = (visual.background as string) ?? "#000";
  const layers = (visual.layers ?? []) as LayerDef[];

  return (
    <AbsoluteFill style={{ background }}>
      {layers.map((layer, idx) => (
        <Layer key={idx} layer={layer} frame={frame} fps={fps} />
      ))}
    </AbsoluteFill>
  );
};
