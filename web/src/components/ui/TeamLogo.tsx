"use client";

import { useState } from "react";

/**
 * NFL team logo via ESPN CDN.
 * Maps team abbreviations to ESPN's format (e.g. LA -> lar, WAS -> wsh).
 */
const ESPN_ABBR_MAP: Record<string, string> = {
  LA: "lar", // Rams
  LAR: "lar",
  WAS: "wsh", // Commanders
  WSH: "wsh",
};

function getEspnAbbr(team: string): string {
  const mapped = ESPN_ABBR_MAP[team?.toUpperCase()];
  return mapped ?? team?.toLowerCase() ?? "";
}

interface TeamLogoProps {
  team: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "w-8 h-8 text-xs",
  md: "w-12 h-12 text-sm",
  lg: "w-16 h-16 text-base",
};

export default function TeamLogo({
  team,
  size = "md",
  className = "",
}: TeamLogoProps) {
  const [errored, setErrored] = useState(false);
  const espnAbbr = getEspnAbbr(team);
  const src = `https://a.espncdn.com/i/teamlogos/nfl/500/${espnAbbr}.png`;

  return (
    <div
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-white/10 font-mono font-bold ${sizeClasses[size]} ${className}`}
      title={team}
    >
      {errored ? (
        <span className="text-[#234058]">{team}</span>
      ) : (
        /* eslint-disable-next-line @next/next/no-img-element */
        <img
          src={src}
          alt={team}
          className="h-full w-full object-contain"
          onError={() => setErrored(true)}
        />
      )}
    </div>
  );
}
