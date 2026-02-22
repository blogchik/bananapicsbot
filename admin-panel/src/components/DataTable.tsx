import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ArrowUp, ArrowDown, Inbox } from 'lucide-react';
import { cn } from '@/lib/utils';

// --- Types ---

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  width?: string;
  render?: (row: T) => React.ReactNode;
  className?: string;
}

export interface PaginationState {
  offset: number;
  limit: number;
  total: number;
}

export interface SortState {
  key: string;
  direction: 'asc' | 'desc';
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  pagination?: PaginationState;
  sort?: SortState;
  onPageChange?: (offset: number) => void;
  onSortChange?: (sort: SortState) => void;
  onRowClick?: (row: T) => void;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
  rowKey?: (row: T) => string | number;
}

// --- Skeleton rows ---

function SkeletonRow({ columns }: { columns: number }) {
  return (
    <tr className="border-b border-surface-lighter/30">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3.5">
          <div className="h-4 bg-surface-light rounded animate-pulse-soft" style={{ width: `${60 + Math.random() * 30}%` }} />
        </td>
      ))}
    </tr>
  );
}

// --- Component ---

export function DataTable<T>({
  columns,
  data,
  loading = false,
  pagination,
  sort,
  onPageChange,
  onSortChange,
  onRowClick,
  emptyMessage = 'No data found.',
  emptyIcon,
  rowKey,
}: DataTableProps<T>) {
  const currentPage = pagination ? Math.floor(pagination.offset / pagination.limit) + 1 : 1;
  const totalPages = pagination ? Math.max(1, Math.ceil(pagination.total / pagination.limit)) : 1;

  function handleSort(key: string) {
    if (!onSortChange) return;
    if (sort?.key === key) {
      onSortChange({ key, direction: sort.direction === 'asc' ? 'desc' : 'asc' });
    } else {
      onSortChange({ key, direction: 'asc' });
    }
  }

  function handleGoToPage(page: number) {
    if (!onPageChange || !pagination) return;
    const newOffset = (page - 1) * pagination.limit;
    onPageChange(Math.max(0, Math.min(newOffset, (totalPages - 1) * pagination.limit)));
  }

  return (
    <div className="card-admin overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto scrollbar-thin">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-lighter/50">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    'px-4 py-3 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider whitespace-nowrap',
                    col.sortable && 'cursor-pointer select-none hover:text-white transition-colors',
                    col.className,
                  )}
                  style={col.width ? { width: col.width } : undefined}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                >
                  <span className="inline-flex items-center gap-1.5">
                    {col.header}
                    {col.sortable && sort?.key === col.key && (
                      sort.direction === 'asc' ? (
                        <ArrowUp className="w-3 h-3 text-banana-500" />
                      ) : (
                        <ArrowDown className="w-3 h-3 text-banana-500" />
                      )
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <SkeletonRow key={i} columns={columns.length} />
              ))
            ) : data.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-16">
                  <div className="flex flex-col items-center justify-center text-center">
                    {emptyIcon || (
                      <div className="w-12 h-12 rounded-xl bg-surface-light flex items-center justify-center mb-3">
                        <Inbox className="w-6 h-6 text-muted" />
                      </div>
                    )}
                    <p className="text-sm text-muted-foreground">{emptyMessage}</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={rowKey ? rowKey(row) : index}
                  className={cn(
                    'border-b border-surface-lighter/30 transition-colors duration-100',
                    onRowClick && 'cursor-pointer hover:bg-surface-light/50',
                  )}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                >
                  {columns.map((col) => (
                    <td key={col.key} className={cn('px-4 py-3.5 text-white whitespace-nowrap', col.className)}>
                      {col.render
                        ? col.render(row)
                        : String((row as Record<string, unknown>)[col.key] ?? '-')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && pagination.total > 0 && (
        <div className="flex items-center gap-2 px-4 py-3 border-t border-surface-lighter/50">
          {/* Showing X-Y of Z — hidden on very small screens */}
          <p className="text-xs text-muted-foreground hidden sm:block mr-auto">
            Showing{' '}
            <span className="text-white font-medium">{pagination.offset + 1}</span>
            {' - '}
            <span className="text-white font-medium">
              {Math.min(pagination.offset + pagination.limit, pagination.total)}
            </span>
            {' of '}
            <span className="text-white font-medium">{pagination.total.toLocaleString()}</span>
          </p>
          <div className="flex items-center gap-1 ml-auto sm:ml-0">
            <button
              onClick={() => handleGoToPage(1)}
              disabled={currentPage === 1}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-white hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="First page"
            >
              <ChevronsLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleGoToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-white hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Previous page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 text-xs text-muted-foreground whitespace-nowrap">
              <span className="text-white font-medium">{currentPage}</span>
              {' / '}
              <span className="text-white font-medium">{totalPages}</span>
            </span>
            <button
              onClick={() => handleGoToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-white hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Next page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleGoToPage(totalPages)}
              disabled={currentPage === totalPages}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-foreground hover:text-white hover:bg-surface-light disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              title="Last page"
            >
              <ChevronsRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
