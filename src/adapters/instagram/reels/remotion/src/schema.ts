import { z } from "zod";

export const visualPropsSchema = z.record(z.string(), z.unknown());

export const transitionSchema = z.object({
  type: z.string().default("none"),
  durationFrames: z.number().int().default(0),
  direction: z.string().default(""),
  easing: z.string().default(""),
});

export const beatSchema = z.object({
  id: z.string(),
  scene: z.string(),
  audioSrc: z.string(),
  durationFrames: z.number().int().positive(),
  visual: visualPropsSchema,
  subtitle: z.string().default(""),
  entryTransition: transitionSchema.default({
    type: "none",
    durationFrames: 0,
    direction: "",
    easing: "",
  }),
  exitTransition: transitionSchema.default({
    type: "none",
    durationFrames: 0,
    direction: "",
    easing: "",
  }),
});

export const reelPropsSchema = z.object({
  fps: z.number().int().positive().default(30),
  beats: z.array(beatSchema).min(1),
});

export type TransitionProps = z.infer<typeof transitionSchema>;
export type BeatProps = z.infer<typeof beatSchema>;
export type ReelProps = z.infer<typeof reelPropsSchema>;
export type VisualProps = z.infer<typeof visualPropsSchema>;
