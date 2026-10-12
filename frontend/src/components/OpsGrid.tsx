import { AgGridReact } from "ag-grid-react";
import type { ColDef, RowClickedEvent } from "ag-grid-community";
import { useMemo } from "react";
import EmptyState from "./EmptyState";
import Skeleton from "./Skeleton";

interface Props<T> {
  rows: T[] | null;
  cols: ColDef<T>[];
  loading?: boolean;
  empty: { note: string; text: string };
  onRowClicked?: (row: T) => void;
  height?: number;
}

/** Thin AG Grid wrapper with the shared theme (DESIGN.md 6.9). Flat, readable, never rotated. */
export default function OpsGrid<T>({ rows, cols, loading, empty, onRowClicked, height = 460 }: Props<T>) {
  const defaultColDef = useMemo<ColDef>(() => ({ sortable: true, resizable: true, flex: 1, minWidth: 110 }), []);
  if (loading && !rows) return <Skeleton rows={5} />;
  if (rows && rows.length === 0) return <EmptyState {...empty} />;
  return (
    <div className="card !p-0 overflow-hidden">
      <div className="ag-theme-quartz" style={{ height, width: "100%" }}>
        <AgGridReact<T>
          rowData={rows ?? []}
          columnDefs={cols}
          defaultColDef={defaultColDef}
          animateRows={false}
          suppressCellFocus
          onRowClicked={onRowClicked ? (e: RowClickedEvent<T>) => e.data && onRowClicked(e.data) : undefined}
        />
      </div>
    </div>
  );
}
