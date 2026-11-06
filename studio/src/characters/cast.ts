import type { CharacterSpec } from "./Character";
import data from "../data/cast.json";
import generated from "../data/generated_assets.json";

/**
 * Cast is loaded from `data/cast.json` so the renderer and the Python pipeline
 * read the same identity record. Forged characters are merged from the same
 * generated render data the catalogue validates; canonical identities win.
 */
type CastFile = {
  characters: Record<string, Omit<CharacterSpec, "id"> & { id: string; role: string; voice: string }>;
};

const file = data as unknown as CastFile;
const generatedFile = generated as unknown as { characters?: CastFile["characters"] };
const merged: CastFile["characters"] = { ...file.characters };
for (const [key, value] of Object.entries(generatedFile.characters ?? {})) {
  if (!(key in merged)) merged[key] = value;
}

export const cast: Record<string, CharacterSpec> = Object.fromEntries(
  Object.entries(merged).map(([key, value]) => [
    key,
    {
      id: value.id,
      name: value.name,
      coat: value.coat,
      coatDark: value.coatDark,
      hat: value.hat,
      hatBand: value.hatBand,
      height: value.height,
      headRadius: value.headRadius,
      hatStyle: value.hatStyle,
      hairStyle: value.hairStyle,
      facialHair: value.facialHair,
      voice: value.voice,
      role: value.role,
    } as CharacterSpec,
  ])
);
