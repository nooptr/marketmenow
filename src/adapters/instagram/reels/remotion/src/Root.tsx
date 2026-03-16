import { Composition } from "remotion";
import { reelPropsSchema } from "./schema";
import type { ReelProps } from "./schema";
import { SceneRouter } from "./SceneRouter";

const calculateDuration = (props: ReelProps): number => {
  return props.beats.reduce((sum, beat) => sum + beat.durationFrames, 0);
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="GradeThisReel"
        component={SceneRouter}
        schema={reelPropsSchema}
        defaultProps={{
          fps: 30,
          beats: [],
        }}
        calculateMetadata={async ({ props }) => {
          const totalFrames = calculateDuration(props);
          return {
            durationInFrames: Math.max(totalFrames, 1),
            fps: props.fps,
            width: 1080,
            height: 1920,
          };
        }}
      />
    </>
  );
};
