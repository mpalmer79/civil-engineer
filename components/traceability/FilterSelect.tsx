import { humanizeStatus } from "@/components/StatusChip";

// Labeled filter dropdown for the traceability matrix filter bar.
export default function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">
      <span className="block">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        aria-label={label}
        className="mt-1 rounded-md border border-slate-300 px-2 py-1.5 text-sm font-normal normal-case text-slate-700"
      >
        <option value="all">All</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {humanizeStatus(opt)}
          </option>
        ))}
      </select>
    </label>
  );
}
