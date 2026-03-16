from __future__ import annotations

import asyncio
import json
import math
import subprocess
from pathlib import Path
from uuid import uuid4

from marketmenow.models.content import MediaAsset, Reel

from ..grading.models import RubricItem
from ..grading.service import SimpleGradingService
from ..settings import InstagramSettings
from .models import AudioType, BeatDefinition, ReelScript, ResolvedBeat
from .script import ReelScriptGenerator
from .template_loader import ReelTemplateLoader
from .tts import TTSProvider, TTSService
from .tts_backends import create_tts_service


class ReelOrchestrator:
    """End-to-end pipeline: template + assignment image -> rendered .mp4 Reel."""

    def __init__(self, settings: InstagramSettings) -> None:
        self._settings = settings
        self._output_dir = settings.output_dir / "reels"
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._loader = ReelTemplateLoader()
        self._grader = SimpleGradingService(
            project=settings.vertex_ai_project,
            location=settings.vertex_ai_location,
        )
        self._script_gen = ReelScriptGenerator(
            grading_service=self._grader,
            vertex_project=settings.vertex_ai_project,
            vertex_location=settings.vertex_ai_location,
        )
        self._tts: TTSService = create_tts_service(
            provider=TTSProvider(settings.tts_provider),
            output_dir=settings.output_dir,
            elevenlabs_api_key=settings.elevenlabs_api_key,
            elevenlabs_voice_id=settings.elevenlabs_voice_id,
            openai_api_key=settings.openai_api_key,
            openai_voice=settings.openai_tts_voice,
            openai_model=settings.openai_tts_model,
        )
        self._remotion_dir = settings.remotion_project_dir

    async def create_reel(
        self,
        assignment_image: Path,
        template_id: str = "can_ai_grade_this",
        rubric_items: list[RubricItem] | None = None,
        caption: str = "",
        hashtags: list[str] | None = None,
    ) -> Reel:
        """Full pipeline: grade -> script -> TTS -> render -> Reel model."""
        template = self._loader.load(template_id)
        variables, resolved_beats = await self._script_gen.generate(
            template=template,
            assignment_image=assignment_image,
            rubric_items=rubric_items,
        )

        beats_with_audio = await self._synthesize_all(
            resolved_beats, template.fps
        )

        reel_script = ReelScript(
            template_id=template.id,
            fps=template.fps,
            aspect_ratio=template.aspect_ratio,
            total_duration_frames=sum(b.duration_frames for b in beats_with_audio),
            beats=beats_with_audio,
            variables=variables,
        )

        output_path = await self._render(reel_script)

        video_asset = MediaAsset(
            uri=str(output_path.resolve()),
            mime_type="video/mp4",
            width=1080,
            height=1920,
        )

        return Reel(
            video=video_asset,
            caption=caption or f"Can our AI grade this? 🤖📝",
            hashtags=hashtags or ["AIGrading", "EdTech", "Wayground"],
        )

    async def _synthesize_all(
        self,
        beats: list[BeatDefinition],
        fps: int,
    ) -> list[ResolvedBeat]:
        """Synthesize TTS / resolve SFX for each beat, computing frame durations."""
        resolved: list[ResolvedBeat] = []

        for beat in beats:
            if beat.audio.type == AudioType.TTS and beat.audio.text:
                synth = await self._tts.synthesize(beat.audio.text)
                audio_path = str(synth.audio_path.resolve())
                duration_sec = synth.duration_seconds + beat.pad_seconds
            elif beat.audio.type == AudioType.SFX and beat.audio.file:
                sfx_path = self._resolve_sfx_path(beat.audio.file)
                audio_path = str(sfx_path)
                duration_sec = await self._tts.get_audio_duration(sfx_path) + beat.pad_seconds
            else:
                audio_path = ""
                duration_sec = 2.0 + beat.pad_seconds

            duration_frames = max(1, math.ceil(duration_sec * fps))

            resolved.append(
                ResolvedBeat(
                    id=beat.id,
                    scene=beat.scene,
                    audio_path=audio_path,
                    duration_seconds=duration_sec,
                    duration_frames=duration_frames,
                    visual=beat.visual,
                )
            )

        return resolved

    def _resolve_sfx_path(self, relative_path: str) -> Path:
        """Resolve an SFX file path relative to the reels package directory."""
        base = Path(__file__).resolve().parent
        candidate = base / relative_path
        if candidate.exists():
            return candidate
        return Path(relative_path)

    async def _render(self, script: ReelScript) -> Path:
        """Write props JSON and invoke Remotion CLI to render the video."""
        props = {
            "fps": script.fps,
            "beats": [
                {
                    "id": b.id,
                    "scene": b.scene,
                    "audioSrc": b.audio_path,
                    "durationFrames": b.duration_frames,
                    "visual": b.visual,
                }
                for b in script.beats
            ],
        }

        run_id = uuid4().hex[:8]
        props_path = self._output_dir / f"props_{run_id}.json"
        props_path.write_text(json.dumps(props, indent=2, default=str))

        output_path = self._output_dir / f"reel_{run_id}.mp4"

        cmd = [
            "npx",
            "remotion",
            "render",
            "src/index.ts",
            "GradeThisReel",
            str(output_path.resolve()),
            "--props",
            str(props_path.resolve()),
            "--width", "1080",
            "--height", "1920",
            "--codec", "h264",
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self._remotion_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Remotion render failed (exit {proc.returncode}):\n"
                f"{stderr.decode()}"
            )

        return output_path
