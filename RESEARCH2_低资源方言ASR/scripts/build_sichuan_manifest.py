"""Build manifests for the local Sichuan Dialect Scripted Speech Corpus.

The archive is read in-place. Audio is not extracted by this script; the
generated ``audio_path`` points to the path that will be used after the
archive is extracted under ``data_raw``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


def read_tsv(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    with zf.open(name) as raw:
        text = raw.read().decode("utf-8-sig")
    return list(csv.DictReader(text.splitlines(), delimiter="\t"))


def read_speakers(zf: zipfile.ZipFile, name: str) -> dict[str, dict[str, str]]:
    rows = read_tsv(zf, name)
    return {row["SPEAKER_ID"]: row for row in rows if row.get("SPEAKER_ID")}


def assign_speaker_splits(
    speaker_to_region: dict[str, str], seed: int
) -> dict[str, str]:
    """Make a speaker-disjoint split while covering every region in test.

    Regions with two speakers get one train and one test speaker. Regions with
    at least three speakers get one train, one dev, and one test speaker.
    """
    by_region: defaultdict[str, list[str]] = defaultdict(list)
    for speaker, region in speaker_to_region.items():
        by_region[region].append(speaker)

    split: dict[str, str] = {}
    for region in sorted(by_region):
        speakers = sorted(by_region[region])
        random.Random(f"{seed}:{region}").shuffle(speakers)
        if len(speakers) == 1:
            split[speakers[0]] = "train"
        elif len(speakers) == 2:
            split[speakers[0]] = "train"
            split[speakers[1]] = "test"
        else:
            split[speakers[0]] = "train"
            split[speakers[1]] = "dev"
            for speaker in speakers[2:]:
                split[speaker] = "train"
            split[speakers[-1]] = "test"
    return split


def build_manifest(archive: Path, output_dir: Path, seed: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, object]] = []
    all_speakers: dict[str, dict[str, str]] = {}
    speaker_to_region: dict[str, str] = {}
    archive_audio: set[str] = set()

    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        for name in names:
            if name.lower().endswith(".wav"):
                archive_audio.add(name.rstrip("/"))

        regions = sorted(
            name.split("/", 1)[0]
            for name in names
            if name.endswith("/SPKINFO.txt")
        )

        for region in regions:
            speaker_file = f"{region}/SPKINFO.txt"
            utterance_file = f"{region}/UTTERANCEINFO.txt"
            speakers = read_speakers(zf, speaker_file)
            all_speakers.update(speakers)
            speaker_to_region.update(
                {speaker_id: region for speaker_id in speakers}
            )

            for row in read_tsv(zf, utterance_file):
                speaker_id = row.get("SPEAKER_ID", "").strip()
                utt_id = row.get("UTTRANS_ID", "").strip()
                text = row.get("TRANSCRIPTION", "").strip()
                if not speaker_id or not utt_id or not text:
                    continue

                internal_audio = f"{region}/WAV/{speaker_id}/{utt_id}"
                records.append(
                    {
                        "utt_id": f"{region}_{utt_id[:-4] if utt_id.lower().endswith('.wav') else utt_id}",
                        "region": region,
                        "speaker_id": speaker_id,
                        "gender": speakers.get(speaker_id, {}).get("GENDER", ""),
                        "age": speakers.get(speaker_id, {}).get("AGE", ""),
                        "text": text,
                        "text_type": "single_reference_transcription",
                        "archive_audio": internal_audio,
                        "audio_path": f"data_raw/{internal_audio}",
                        "audio_in_archive": internal_audio in archive_audio,
                    }
                )

    speaker_split = assign_speaker_splits(speaker_to_region, seed)
    for record in records:
        record["split"] = speaker_split[record["speaker_id"]]

    records.sort(key=lambda item: str(item["utt_id"]))
    all_path = output_dir / "sichuan_all.jsonl"
    with all_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    for split in ("train", "dev", "test"):
        split_path = output_dir / f"sichuan_{split}.jsonl"
        with split_path.open("w", encoding="utf-8", newline="\n") as handle:
            for record in records:
                if record["split"] == split:
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    by_region = Counter(str(record["region"]) for record in records)
    by_split = Counter(str(record["split"]) for record in records)
    speakers_by_split: defaultdict[str, set[str]] = defaultdict(set)
    for record in records:
        speakers_by_split[str(record["split"])].add(str(record["speaker_id"]))

    summary = {
        "archive": str(archive),
        "seed": seed,
        "records_with_text": len(records),
        "speakers": len(all_speakers),
        "regions": sorted(by_region),
        "records_by_region": dict(sorted(by_region.items())),
        "records_by_split": dict(sorted(by_split.items())),
        "speakers_by_split": {
            key: sorted(value) for key, value in sorted(speakers_by_split.items())
        },
        "missing_audio_entries": sum(
            1 for record in records if not record["audio_in_archive"]
        ),
        "note": (
            "The corpus currently exposes one TRANSCRIPTION field only; this "
            "manifest does not claim a paired normalized-text target."
        ),
    }
    (output_dir / "sichuan_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20260920)
    args = parser.parse_args()
    build_manifest(args.archive, args.output_dir, args.seed)


if __name__ == "__main__":
    main()
