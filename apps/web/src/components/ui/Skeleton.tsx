export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-md bg-muted ${className}`}
      aria-hidden="true"
    />
  );
}

export function GraphSkeleton() {
  return (
    <div className="flex h-full flex-col gap-3 p-4">
      <div className="flex items-center gap-3">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>
      <div className="relative flex-1 overflow-hidden rounded-lg border border-border">
        <div className="absolute left-[12%] top-[30%] h-14 w-32 rounded-lg bg-muted" />
        <div className="absolute left-[45%] top-[18%] h-14 w-32 rounded-lg bg-muted" />
        <div className="absolute left-[48%] top-[58%] h-14 w-32 rounded-lg bg-muted" />
        <div className="absolute left-[76%] top-[36%] h-14 w-32 rounded-lg bg-muted" />
        <div className="absolute left-[24%] top-[35%] h-px w-[20%] bg-border" />
        <div className="absolute left-[56%] top-[30%] h-px w-[18%] bg-border" />
        <div className="absolute left-[27%] top-[45%] h-[14%] w-px bg-border" />
      </div>
    </div>
  );
}

export function ListSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-4 w-4 rounded-full" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-3.5 w-3/4" />
            <Skeleton className="h-3 w-1/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SearchResultsSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="rounded-lg border border-border p-3">
          <Skeleton className="mb-2 h-3.5 w-2/3" />
          <Skeleton className="h-3 w-full" />
          <div className="mt-2 flex gap-1.5">
            <Skeleton className="h-3.5 w-14" />
            <Skeleton className="h-3.5 w-20" />
          </div>
        </div>
      ))}
    </div>
  );
}
