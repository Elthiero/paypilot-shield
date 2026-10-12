export default function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="h-12 border border-dashed border-ink bg-skeleton rounded" style={{ animation: "pulse2 1.2s ease-in-out infinite" }} />
      ))}
    </div>
  );
}
