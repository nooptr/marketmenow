import { Audio, Series, staticFile } from "remotion";
import type { BeatProps, ReelProps, VisualProps } from "./schema";
import {
  GradingScene,
  HookScene,
  ReactionScene,
  ResultScene,
  RevealScene,
  RubricScene,
  TransitionScene,
} from "./scenes";

type SceneComponent = React.FC<{ visual: VisualProps }>;

const SCENE_MAP: Record<string, SceneComponent> = {
  HookScene,
  RevealScene,
  ReactionScene,
  TransitionScene,
  RubricScene,
  GradingScene,
  ResultScene,
};

export const SceneRouter: React.FC<ReelProps> = ({ beats }) => {
  return (
    <Series>
      {beats.map((beat) => {
        const Scene = SCENE_MAP[beat.scene];
        if (!Scene) {
          console.warn(`Unknown scene: ${beat.scene}`);
          return null;
        }

        return (
          <Series.Sequence
            key={beat.id}
            durationInFrames={beat.durationFrames}
          >
            <Scene visual={beat.visual} />
            {beat.audioSrc && (
              <Audio src={beat.audioSrc} volume={1} />
            )}
          </Series.Sequence>
        );
      })}
    </Series>
  );
};
