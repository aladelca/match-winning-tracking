import type { Probabilities } from "@/lib/types";
import { cn, formatPercent } from "@/lib/utils";

export interface PredictionBarProps {
  probabilities: Probabilities;
  size?: "sm" | "md" | "lg";
  showLabels?: boolean;
  className?: string;
}

export function PredictionBar({
  probabilities,
  size = "md",
  showLabels = true,
  className,
}: PredictionBarProps) {
  const heights = {
    sm: "h-2",
    md: "h-3",
    lg: "h-5",
  } as const;

  return (
    <div className={cn("w-full space-y-2", className)}>
      <div
        className={cn(
          "flex w-full overflow-hidden rounded-full bg-muted",
          heights[size],
        )}
        aria-label="Probabilidades"
      >
        <div
          className="bg-[hsl(var(--home))]"
          style={{ width: `${probabilities.home * 100}%` }}
        />
        <div
          className="bg-[hsl(var(--draw))]"
          style={{ width: `${probabilities.draw * 100}%` }}
        />
        <div
          className="bg-[hsl(var(--away))]"
          style={{ width: `${probabilities.away * 100}%` }}
        />
      </div>
      {showLabels && (
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[hsl(var(--home))]" />
            <span className="font-medium">Local</span>
            <span className="text-muted-foreground">
              {formatPercent(probabilities.home)}
            </span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[hsl(var(--draw))]" />
            <span className="font-medium">Empate</span>
            <span className="text-muted-foreground">
              {formatPercent(probabilities.draw)}
            </span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-[hsl(var(--away))]" />
            <span className="font-medium">Visita</span>
            <span className="text-muted-foreground">
              {formatPercent(probabilities.away)}
            </span>
          </span>
        </div>
      )}
    </div>
  );
}
