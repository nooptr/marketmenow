import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  Easing,
} from "remotion";
import type { TransitionProps } from "../schema";

type EasingFn = (t: number) => number;

const EASING_MAP: Record<string, EasingFn> = {
  linear: Easing.linear,
  "ease-in": Easing.ease,
  "ease-out": Easing.out(Easing.ease),
  "ease-in-out": Easing.inOut(Easing.ease),
  bounce: Easing.bounce,
};

function getEasing(name: string): EasingFn | undefined {
  return name ? EASING_MAP[name] : undefined;
}

function getDirectionTranslate(
  direction: string,
  progress: number,
): { translateX: number; translateY: number } {
  const offset = interpolate(progress, [0, 1], [100, 0]);
  switch (direction) {
    case "left":
      return { translateX: -offset, translateY: 0 };
    case "right":
      return { translateX: offset, translateY: 0 };
    case "down":
      return { translateX: 0, translateY: offset };
    case "up":
    default:
      return { translateX: 0, translateY: -offset };
  }
}

function computeTransitionStyle(
  transition: TransitionProps,
  progress: number,
): React.CSSProperties {
  switch (transition.type) {
    case "fade":
      return { opacity: progress };
    case "slide": {
      const { translateX, translateY } = getDirectionTranslate(
        transition.direction || "up",
        progress,
      );
      return {
        transform: `translate(${translateX}%, ${translateY}%)`,
      };
    }
    case "scale": {
      const scale = interpolate(progress, [0, 1], [0.5, 1]);
      return { transform: `scale(${scale})`, opacity: progress };
    }
    case "wipe": {
      const dir = transition.direction || "left";
      const pct = `${Math.round(progress * 100)}%`;
      let clip: string;
      switch (dir) {
        case "right":
          clip = `inset(0 0 0 ${100 - progress * 100}%)`;
          break;
        case "up":
          clip = `inset(0 0 ${100 - progress * 100}% 0)`;
          break;
        case "down":
          clip = `inset(${100 - progress * 100}% 0 0 0)`;
          break;
        case "left":
        default:
          clip = `inset(0 ${100 - progress * 100}% 0 0)`;
          break;
      }
      return { clipPath: clip };
    }
    case "none":
    default:
      return {};
  }
}

interface TransitionWrapperProps {
  entryTransition: TransitionProps;
  exitTransition: TransitionProps;
  durationFrames: number;
  children: React.ReactNode;
}

export const TransitionWrapper: React.FC<TransitionWrapperProps> = ({
  entryTransition,
  exitTransition,
  durationFrames,
  children,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isEntryActive =
    entryTransition.type !== "none" && entryTransition.durationFrames > 0;
  const isExitActive =
    exitTransition.type !== "none" && exitTransition.durationFrames > 0;

  if (!isEntryActive && !isExitActive) {
    return <AbsoluteFill>{children}</AbsoluteFill>;
  }

  let style: React.CSSProperties = {};

  if (isEntryActive) {
    const entryDur = entryTransition.durationFrames;
    let entryProgress: number;

    if (entryTransition.type === "spring") {
      entryProgress = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 },
        durationInFrames: entryDur,
      });
    } else {
      const easing = getEasing(entryTransition.easing);
      entryProgress = interpolate(frame, [0, entryDur], [0, 1], {
        extrapolateRight: "clamp",
        extrapolateLeft: "clamp",
        ...(easing ? { easing } : {}),
      });
    }

    const entryStyle = computeTransitionStyle(entryTransition, entryProgress);
    style = { ...style, ...entryStyle };
  }

  if (isExitActive) {
    const exitDur = exitTransition.durationFrames;
    const exitStart = durationFrames - exitDur;

    if (frame >= exitStart) {
      let exitProgress: number;
      const localFrame = frame - exitStart;

      if (exitTransition.type === "spring") {
        exitProgress = spring({
          frame: localFrame,
          fps,
          config: { damping: 12, stiffness: 100 },
          durationInFrames: exitDur,
        });
      } else {
        const easing = getEasing(exitTransition.easing);
        exitProgress = interpolate(localFrame, [0, exitDur], [0, 1], {
          extrapolateRight: "clamp",
          extrapolateLeft: "clamp",
          ...(easing ? { easing } : {}),
        });
      }

      // Exit is inverse — go from visible to hidden
      const exitStyle = computeTransitionStyle(
        exitTransition,
        1 - exitProgress,
      );
      style = { ...style, ...exitStyle };
    }
  }

  return <AbsoluteFill style={style}>{children}</AbsoluteFill>;
};
